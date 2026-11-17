"""Rule-engine and extraction tests. Run: python -m unittest discover -s tests"""

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.danger import detect
from app.dialog import build_readback, parse_correction
from app.extract import extract_rules
from app.followups import build_followups
from app.normalize import normalise, parse_date, parse_weight

TODAY = date(2026, 11, 15)

DEMO_1 = (
    "Lakshmi, beneficiary ID ASHA102. Pregnancy visit. Weight 55 kilo. "
    "ANC completed. IFA tablets given. Next visit November 20."
)

# Verbatim output of a real Gnani round-trip without keyterms (noisy).
DEMO_1_NOISY = (
    "Lakshmi, beneficiary ID ASHAH 102, pregnancy visit weight 55 kilo. "
    "Hence he completed Tifa tablets given next visit 20 November."
)

DEMO_1_TAMIL = (
    "லக்ஷ்மி, பயனாளி ID ASHAE102 கர்ப்பகால பரிசோதனை முடிந்தது. "
    "எடை 55 kg IFA மாத்திரை கொடுத்தேன் அடுத்த வருகை 20 November."
)


class NormaliseTests(unittest.TestCase):
    def test_asr_id_repair(self) -> None:
        self.assertIn("ASHA102", normalise("beneficiary ID ASHAH 102"))
        self.assertIn("ASHA102", normalise("ID ASHAE102"))
        self.assertIn("ASHA102", normalise("asha 102"))

    def test_medical_alias_repair(self) -> None:
        self.assertIn("IFA", normalise("Tifa tablets given"))

    def test_number_words(self) -> None:
        self.assertEqual(parse_weight(normalise("weight is fifty five kilo")).kg, 55.0)
        self.assertEqual(parse_weight(normalise("weight 55.5 kg")).kg, 55.5)
        self.assertEqual(parse_weight(normalise("எடை 2.8 கிலோ")).kg, 2.8)

    def test_dates(self) -> None:
        self.assertEqual(parse_date("next visit November 20", TODAY).value, date(2026, 11, 20))
        self.assertEqual(parse_date("next visit 20th November", TODAY).value, date(2026, 11, 20))
        self.assertEqual(parse_date("அடுத்த வருகை 20 November", TODAY).value, date(2026, 11, 20))
        self.assertEqual(parse_date("next visit 20/11/2026", TODAY).value, date(2026, 11, 20))
        self.assertEqual(parse_date("next visit 20.11.2026", TODAY).value, date(2026, 11, 20))
        # Decimal weights must never become dates.
        self.assertIsNone(parse_date("Weight 2.8 kilo", TODAY))
        # A December date seen in November stays this year.
        self.assertEqual(parse_date("next visit December 5", TODAY).value, date(2026, 12, 5))
        # A date already past rolls to next year.
        self.assertEqual(parse_date("next visit November 1", TODAY).value, date(2027, 11, 1))


class ExtractionTests(unittest.TestCase):
    def test_demo_1(self) -> None:
        record = extract_rules(DEMO_1, today=TODAY)
        self.assertEqual(record.beneficiary_id, "ASHA102")
        self.assertEqual(record.patient_name, "Lakshmi")
        self.assertEqual(record.visit_type, "pregnancy_anc")
        self.assertEqual(record.weight_kg, 55.0)
        self.assertIs(record.anc_completed, True)
        self.assertIs(record.ifa_provided, True)
        self.assertEqual(record.next_visit_date, "2026-11-20")
        self.assertEqual(record.missing(), [])

    def test_noisy_asr_still_extracts(self) -> None:
        record = extract_rules(DEMO_1_NOISY, today=TODAY)
        self.assertEqual(record.beneficiary_id, "ASHA102")
        self.assertEqual(record.weight_kg, 55.0)
        self.assertIs(record.anc_completed, True)
        self.assertIs(record.ifa_provided, True)

    def test_tamil_note(self) -> None:
        record = extract_rules(DEMO_1_TAMIL, language="ta-IN", today=TODAY)
        self.assertEqual(record.beneficiary_id, "ASHA102")
        self.assertEqual(record.weight_kg, 55.0)
        self.assertEqual(record.visit_type, "pregnancy_anc")
        self.assertEqual(record.next_visit_date, "2026-11-20")
        self.assertIs(record.ifa_provided, True)

    def test_clinical_phrase_is_not_a_name(self) -> None:
        record = extract_rules("கர்ப்பகால பரிசோதனை, எடை 55 கிலோ", language="ta-IN", today=TODAY)
        self.assertIsNone(record.patient_name)

    def test_missing_fields_are_not_invented(self) -> None:
        record = extract_rules("Pregnancy visit completed. She is fine.", today=TODAY)
        self.assertIsNone(record.patient_name)
        self.assertIsNone(record.beneficiary_id)
        self.assertIsNone(record.weight_kg)
        self.assertIn("beneficiary_id", record.missing())
        self.assertIn("weight_kg", record.missing())

    def test_newborn_note(self) -> None:
        record = extract_rules("Newborn has high fever. Weight 2.8 kilo.", today=TODAY)
        self.assertEqual(record.visit_type, "newborn_hbnc")
        self.assertEqual(record.weight_kg, 2.8)
        self.assertIsNone(record.next_visit_date)

    def test_hbnc_confusion_in_pregnancy_note_is_anc(self) -> None:
        record = extract_rules(
            "Lakshmi, ID ASHA102, pregnancy visit, weight 55 kilo. HBNC completed.",
            today=TODAY,
        )
        self.assertIs(record.anc_completed, True)

    def test_hbnc_in_newborn_note_does_not_set_anc(self) -> None:
        record = extract_rules("Newborn HBNC completed. Weight 2.8 kilo.", today=TODAY)
        self.assertIsNone(record.anc_completed)


class DangerTests(unittest.TestCase):
    def test_bleeding_flags(self) -> None:
        result = detect("She has heavy bleeding during pregnancy.", visit_type="pregnancy_anc")
        self.assertTrue(result.has_danger)
        self.assertIn("vaginal_bleeding", [hit.code for hit in result.hits])

    def test_negated_bleeding_does_not_flag(self) -> None:
        for phrase in (
            "There is no bleeding.",
            "She has no bleeding, no discharge.",
            "Bleeding illa.",
            "இரத்தப்போக்கு இல்லை.",
            "कोई खून नहीं है।",
            "Patient denies bleeding.",
        ):
            with self.subTest(phrase=phrase):
                result = detect(phrase, visit_type="pregnancy_anc")
                self.assertFalse(
                    result.has_danger,
                    f"false alert for: {phrase} -> {[h.code for h in result.hits]}",
                )

    def test_no_danger_signs(self) -> None:
        result = detect("No danger signs mentioned. She is fine.", visit_type="pregnancy_anc")
        self.assertFalse(result.has_danger)
        self.assertTrue(result.all_clear)

    def test_newborn_fever_is_newborn_category(self) -> None:
        result = detect("Newborn has high fever.", visit_type="newborn_hbnc")
        self.assertTrue(result.has_danger)
        self.assertEqual(result.hits[0].category, "newborn")

    def test_mother_fever_is_pregnancy_category(self) -> None:
        result = detect("Patient has high fever and weakness.", visit_type="pregnancy_anc")
        self.assertTrue(result.has_danger)
        self.assertEqual(result.hits[0].category, "pregnancy")

    def test_no_fever_is_not_flagged(self) -> None:
        result = detect("She has no fever.", visit_type="pregnancy_anc")
        self.assertFalse(result.has_danger)

    def test_postpartum_bleeding(self) -> None:
        result = detect("Heavy bleeding after delivery.", visit_type="postnatal")
        self.assertTrue(result.has_danger)

    def test_low_birth_weight_numeric_rule(self) -> None:
        result = detect("Weight 2.1 kilo.", visit_type="newborn_hbnc", weight_kg=2.1)
        self.assertIn("low_birth_weight", [hit.code for hit in result.hits])
        ok = detect("Weight 2.8 kilo.", visit_type="newborn_hbnc", weight_kg=2.8)
        self.assertNotIn("low_birth_weight", [hit.code for hit in ok.hits])

    def test_tamil_danger_sign(self) -> None:
        result = detect("கடுமையான தலைவலி இருக்கிறது.", language="ta-IN", visit_type="pregnancy_anc")
        self.assertIn("severe_headache", [hit.code for hit in result.hits])

    def test_postpartum_fever_flags_infection(self) -> None:
        result = detect("Fever after delivery.", visit_type="postnatal")
        self.assertIn("postpartum_infection", [hit.code for hit in result.hits])

    def test_warm_newborn_is_not_hypothermia(self) -> None:
        result = detect("Newborn body is warm and feeding well.", visit_type="newborn_hbnc")
        self.assertFalse(result.has_danger, [hit.code for hit in result.hits])

    def test_fasting_is_not_fast_breathing(self) -> None:
        result = detect("Newborn is fasting because of a ritual.", visit_type="newborn_hbnc")
        self.assertNotIn("newborn_fast_breathing", [hit.code for hit in result.hits])

    def test_clean_cord_is_not_umbilical_infection(self) -> None:
        result = detect("கொப்பூழ் சுத்தமாக உள்ளது.", language="ta-IN", visit_type="newborn_hbnc")
        self.assertNotIn("newborn_umbilical_infection", [hit.code for hit in result.hits])


class CorrectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.record = extract_rules(DEMO_1, today=TODAY)

    def test_weight_correction(self) -> None:
        correction = parse_correction("No, weight is 55.5 kilo", self.record, language="en-IN", today=TODAY)
        assert correction is not None
        self.assertEqual(correction.field, "weight_kg")
        self.assertEqual(correction.value, 55.5)
        self.assertIn("55.5", correction.spoken)

    def test_date_correction(self) -> None:
        correction = parse_correction(
            "change next visit to November 22", self.record, language="en-IN", today=TODAY
        )
        assert correction is not None
        self.assertEqual(correction.field, "next_visit_date")
        self.assertEqual(correction.value, "2026-11-22")

    def test_newborn_weight_decimal_is_not_read_as_date(self) -> None:
        # Regression: "2.8" was parsed as day 2 / month 8 when the visit type
        # was still "general", so the correction silently changed the date.
        record = extract_rules("Weight is 2.5 kilo.", today=TODAY)
        correction = parse_correction(
            "No, weight is 2.8 kilo", record, language="en-IN", today=TODAY
        )
        assert correction is not None
        self.assertEqual(correction.field, "weight_kg")
        self.assertEqual(correction.value, 2.8)
        self.assertIn("2.8", correction.spoken)

    def test_name_correction(self) -> None:
        correction = parse_correction(
            "No, the name is Lakshmi Devi", self.record, language="en-IN", today=TODAY
        )
        assert correction is not None
        self.assertEqual(correction.field, "patient_name")

    def test_unmappable_returns_none(self) -> None:
        self.assertIsNone(parse_correction("hello there", self.record, language="en-IN", today=TODAY))


class FollowUpTests(unittest.TestCase):
    def test_urgent_task_first(self) -> None:
        record = extract_rules(DEMO_1, today=TODAY)
        result = detect("Newborn has high fever.", visit_type="newborn_hbnc")
        plan = build_followups(record, result.hits, today=TODAY)
        self.assertEqual(plan.tasks[0].priority, "urgent")
        self.assertEqual(plan.tasks[0].kind, "referral")
        self.assertEqual(plan.tasks[0].due_date, TODAY.isoformat())

    def test_vaccination_verification_task(self) -> None:
        record = extract_rules(DEMO_1, today=TODAY)
        plan = build_followups(record, [], today=TODAY)
        titles = [task.title for task in plan.tasks]
        self.assertIn("Verify vaccination status", titles)

    def test_next_visit_task_uses_spoken_date(self) -> None:
        record = extract_rules(DEMO_1, today=TODAY)
        plan = build_followups(record, [], today=TODAY)
        visit_task = next(task for task in plan.tasks if task.kind == "visit")
        self.assertEqual(visit_task.due_date, "2026-11-20")

    def test_next_visit_title_keeps_acronym(self) -> None:
        record = extract_rules(DEMO_1, today=TODAY)
        plan = build_followups(record, [], today=TODAY)
        visit_task = next(task for task in plan.tasks if task.kind == "visit")
        self.assertEqual(visit_task.title, "Next ANC checkup")
        self.assertNotIn("(anc)", visit_task.title)


class ReadbackTests(unittest.TestCase):
    def test_english_readback(self) -> None:
        record = extract_rules(DEMO_1, today=TODAY)
        text = build_readback(record, "en-IN")
        self.assertIn("Lakshmi", text)
        self.assertIn("55", text)
        self.assertIn("November 20", text)
        self.assertIn("Is this correct?", text)

    def test_missing_field_is_asked(self) -> None:
        record = extract_rules("Pregnancy visit, weight 55 kilo.", today=TODAY)
        text = build_readback(record, "en-IN")
        self.assertIn("I still need", text)

    def test_missing_name_does_not_repeat_patient(self) -> None:
        record = extract_rules("Pregnancy visit, weight 55 kilo.", today=TODAY)
        text = build_readback(record, "en-IN")
        self.assertNotIn("Patient the patient", text)
        self.assertIn("This patient", text)

    def test_visit_label_has_no_parentheses_in_speech(self) -> None:
        record = extract_rules(DEMO_1, today=TODAY)
        text = build_readback(record, "en-IN")
        self.assertNotIn("(ANC)", text)
        self.assertIn("Pregnancy visit", text)

    def test_tamil_readback_without_name(self) -> None:
        record = extract_rules(
            "கர்ப்பகால பரிசோதனை, எடை 55 கிலோ", language="ta-IN", today=TODAY
        )
        text = build_readback(record, "ta-IN")
        self.assertNotIn("நோயாளி நோயாளி", text)
        self.assertIn("இந்த நோயாளி", text)

    def test_tamil_readback(self) -> None:
        record = extract_rules(DEMO_1_TAMIL, language="ta-IN", today=TODAY)
        text = build_readback(record, "ta-IN")
        self.assertIn("நோயாளி", text)
        self.assertIn("நவம்பர் 20", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
