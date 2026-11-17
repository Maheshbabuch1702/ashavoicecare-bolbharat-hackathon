"""Spoken read-back and field-level correction parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher

from .extract import VisitRecord
from .i18n import MONTHS, YES_NO, field_label, t, visit_type_label
from .normalize import (
    fold,
    is_negative,
    normalise,
    parse_date,
    parse_weight,
)

_MONTHS = {
    "en-IN": ["", "January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"],
    "ta-IN": ["", "ஜனவரி", "பிப்ரவரி", "மார்ச்", "ஏப்ரல்", "மே", "ஜூன்", "ஜூலை",
              "ஆகஸ்ட்", "செப்டம்பர்", "அக்டோபர்", "நவம்பர்", "டிசம்பர்"],
    "hi-IN": ["", "जनवरी", "फरवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई",
              "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"],
}


def format_date(iso: str | None, language: str) -> str:
    if not iso:
        return ""
    try:
        parsed = date.fromisoformat(iso)
    except ValueError:
        return iso
    months = _MONTHS.get(language) or _MONTHS["en-IN"]
    if language == "hi-IN":
        return f"{parsed.day} {months[parsed.month]}"
    return f"{months[parsed.month]} {parsed.day}"


def format_weight(value: float | None, language: str) -> str:
    if value is None:
        return ""
    number = f"{value:g}"
    if language == "ta-IN":
        return f"{number} கிலோ"
    if language == "hi-IN":
        return f"{number} किलो"
    return f"{number} kilograms"


def _status_text(key: str, value: bool | None, language: str) -> str:
    if value is None:
        return YES_NO[f"{key}_unknown"][language]
    return YES_NO[f"{key}_{'true' if value else 'false'}"][language]


_PARENTHETICAL = re.compile(r"\s*\([^)]*\)")


def _speech_visit_type(visit_type: str, language: str) -> str:
    """Drop the '(ANC)' / '(HBNC)' gloss so TTS never reads brackets aloud."""
    return _PARENTHETICAL.sub("", visit_type_label(visit_type, language)).strip()


def build_readback(record: VisitRecord, language: str, *, missing: list[str] | None = None) -> str:
    """Compose the sentence the worker hears before saving."""
    missing = missing if missing is not None else record.missing()
    parts: list[str] = []

    if language == "ta-IN":
        parts.append(f"நோயாளி {record.patient_name}" if record.patient_name else "இந்த நோயாளி")
        parts.append(_speech_visit_type(record.visit_type, language))
        if record.weight_kg is not None:
            parts.append(f"எடை {format_weight(record.weight_kg, language)}")
        if record.anc_completed is not None:
            parts.append(f"ANC பரிசோதனை {_status_text('anc', record.anc_completed, language)}")
        if record.ifa_provided is not None:
            parts.append(f"IFA மாத்திரை {_status_text('ifa', record.ifa_provided, language)}")
        if record.vaccination_status == "given":
            parts.append("தடுப்பூசி வழங்கப்பட்டது")
        elif record.vaccination_status == "due":
            parts.append("தடுப்பூசி நிலுவையில் உள்ளது")
        if record.next_visit_date:
            parts.append(f"அடுத்த வருகை {format_date(record.next_visit_date, language)}")
    elif language == "hi-IN":
        parts.append(f"मरीज़ {record.patient_name}" if record.patient_name else "यह मरीज़")
        parts.append(_speech_visit_type(record.visit_type, language))
        if record.weight_kg is not None:
            parts.append(f"वज़न {format_weight(record.weight_kg, language)}")
        if record.anc_completed is not None:
            parts.append(f"ANC जाँच {_status_text('anc', record.anc_completed, language)}")
        if record.ifa_provided is not None:
            parts.append(f"IFA टैबलेट {_status_text('ifa', record.ifa_provided, language)}")
        if record.vaccination_status == "given":
            parts.append("टीकाकरण हो गया")
        elif record.vaccination_status == "due":
            parts.append("टीकाकरण बाकी है")
        if record.next_visit_date:
            parts.append(f"अगली विज़िट {format_date(record.next_visit_date, language)}")
    else:
        parts.append(f"Patient {record.patient_name}" if record.patient_name else "This patient")
        parts.append(_speech_visit_type(record.visit_type, language))
        if record.weight_kg is not None:
            parts.append(f"Weight {format_weight(record.weight_kg, language)}")
        if record.anc_completed is not None:
            parts.append(f"ANC checkup {_status_text('anc', record.anc_completed, language)}")
        if record.ifa_provided is not None:
            parts.append(f"IFA tablets {_status_text('ifa', record.ifa_provided, language)}")
        if record.vaccination_status == "given":
            parts.append("Vaccination given")
        elif record.vaccination_status == "due":
            parts.append("Vaccination is pending")
        if record.next_visit_date:
            parts.append(f"Next visit {format_date(record.next_visit_date, language)}")

    body = ". ".join(part for part in parts if part)
    sentence = f"{body}. {t('confirm_suffix', language)}"

    if missing:
        labels = ", ".join(field_label(name, language) for name in missing)
        prefix = t("missing_prefix", language, fields=labels)
        return f"{prefix} {sentence}"
    return sentence


# --------------------------------------------------------------------------- #
# corrections
# --------------------------------------------------------------------------- #

@dataclass
class Correction:
    field: str
    value: object
    spoken: str
    evidence: str


_WEIGHT_WORDS = ("weight", "wt", "எடை", "वज़न", "वजन", "బరువు")
_DATE_WORDS = ("next visit", "visit date", "date", "அடுத்த வருகை", "தேதி", "अगली विज़िट", "तारीख")
_NAME_WORDS = ("name", "பெயர்", "नाम")
_ID_WORDS = ("id", "ஐடி", "आईडी", "beneficiary")
_ANC_WORDS = ("anc", "checkup", "check up", "பரிசோதனை", "जाँच", "जांच")
_IFA_WORDS = ("ifa", "tablet", "மாதிரை", "மாத்திரை", "टैबलेट", "goli")
_VACCINE_WORDS = ("vaccin", "immuni", "தடுப்பூசி", "टीका", "टीकाकरण")
_VISIT_WORDS = ("visit type", "வருகை வகை", "विज़िट का प्रकार")

# Numeric dates use "/" or "-"; a dot is a decimal point ("2.8 kilo"), so it
# must not make the digit pair look like a date.
_DATE_NUMERIC_HINT = re.compile(r"(?<!\d)\d{1,2}\s*[/\-]\s*\d{1,2}(?!\d)")
_MONTH_HINT = re.compile(
    r"(?<!\w)(?:"
    + "|".join(sorted((re.escape(name) for name in MONTHS), key=len, reverse=True))
    + r")(?!\w)",
    re.IGNORECASE,
)

_CORRECTION_LEAD = re.compile(
    r"^\s*(?:no|nope|not|actually|sorry|wait|change|correct(?:ion)?|"
    r"இல்லை|இல்ல|திருத்தம்|नहीं|गलत|बदलो|रुको)[\s,.]*",
    re.IGNORECASE,
)


def _has_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def _spoken(field: str, value: object, language: str) -> str:
    if field == "weight_kg":
        return format_weight(float(value), language)
    if field == "next_visit_date":
        return format_date(str(value), language)
    if field in {"anc_completed", "ifa_provided"}:
        key = "anc" if field == "anc_completed" else "ifa"
        return _status_text(key, bool(value), language)
    if field == "visit_type":
        return visit_type_label(str(value), language)
    return str(value)


def _weight_plausible(kg: float, record: VisitRecord, lowered: str) -> bool:
    """Sanity-check a corrected weight without rejecting newborn corrections.

    A worker may correct a newborn's weight while the note is still typed as a
    general visit, so accept the newborn range when the record already holds a
    newborn-range weight or the utterance mentions a baby.
    """
    newborn_context = (
        record.visit_type == "newborn_hbnc"
        or (record.weight_kg is not None and record.weight_kg < 12)
        or bool(re.search(r"newborn|new born|baby|infant|குழந்தை|நவஜாத|नवजात|शिशु", lowered))
    )
    if newborn_context:
        return 0.5 <= kg <= 12
    return 20 <= kg <= 200


def parse_correction(
    text: str,
    record: VisitRecord,
    *,
    language: str,
    today: date | None = None,
) -> Correction | None:
    """Map one spoken correction onto exactly one field.

    Returns None when the utterance cannot be mapped, so the caller can ask the
    worker to repeat instead of guessing.
    """
    cleaned = _CORRECTION_LEAD.sub("", text or "").strip()
    normalised = normalise(cleaned)
    lowered = fold(normalised)
    if not lowered:
        return None

    # 1. Weight. Once the utterance names weight, never reinterpret its digits
    #    as a date ("2.8 kilo" is not August 2).
    weight_mentioned = bool(
        _has_any(lowered, _WEIGHT_WORDS)
        or re.search(r"\d\s*(?:kg|kilo|கிலோ|किलो)", lowered)
    )
    if weight_mentioned:
        parsed = parse_weight(normalised)
        if parsed and _weight_plausible(parsed.kg, record, lowered):
            return Correction("weight_kg", parsed.kg, _spoken("weight_kg", parsed.kg, language), parsed.text)
        return None

    # 2. Date.
    if (
        _has_any(lowered, _DATE_WORDS)
        or _DATE_NUMERIC_HINT.search(lowered)
        or _MONTH_HINT.search(lowered)
    ):
        parsed_date = parse_date(normalised, today=today)
        if parsed_date:
            iso = parsed_date.value.isoformat()
            return Correction("next_visit_date", iso, _spoken("next_visit_date", iso, language), parsed_date.text)

    # 3. Beneficiary ID.
    id_match = re.search(r"\b(ASHA\d{2,6})\b", normalised, re.IGNORECASE)
    if id_match:
        value = id_match.group(1).upper()
        return Correction("beneficiary_id", value, value, id_match.group(0))
    if _has_any(lowered, _ID_WORDS):
        digits = re.search(r"\d{3,6}", lowered)
        if digits:
            return Correction("beneficiary_id", digits.group(0), digits.group(0), digits.group(0))

    # 4. Name.
    if _has_any(lowered, _NAME_WORDS):
        match = re.search(r"(?:name|பெயர்|नाम)\s*(?:is)?\s*[:\-]?\s*([^\d.,;]+)", cleaned, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip(" ,.-")
            if candidate:
                return Correction("patient_name", candidate, candidate, match.group(0))

    # 5. ANC / IFA booleans.
    if _has_any(lowered, _ANC_WORDS):
        value = _bool_from_text(lowered)
        if value is not None:
            return Correction("anc_completed", value, _spoken("anc_completed", value, language), lowered)
    if _has_any(lowered, _IFA_WORDS):
        value = _bool_from_text(lowered)
        if value is not None:
            return Correction("ifa_provided", value, _spoken("ifa_provided", value, language), lowered)

    # 6. Vaccination.
    if _has_any(lowered, _VACCINE_WORDS):
        if re.search(r"not|नहीं|இல்ல", lowered):
            return Correction("vaccination_status", "due", _spoken("vaccination_status", "due", language), lowered)
        if re.search(r"given|done|completed|दी|हो गया|கொடுத்த|முடிந்த", lowered):
            return Correction("vaccination_status", "given", "vaccination given", lowered)

    # 7. Visit type.
    if _has_any(lowered, _VISIT_WORDS):
        for candidate, patterns in (
            ("pregnancy_anc", ("pregnancy", "anc", "antenatal", "கர்ப்ப", "गर्भ")),
            ("newborn_hbnc", ("newborn", "new born", "baby", "நவஜாத", "नवजात", "குழந்தை")),
            ("postnatal", ("postnatal", "after delivery", "பிரசவ", "प्रसव")),
            ("immunization", ("immuni", "vaccin", "தடுப்பூசி", "टीका")),
        ):
            if any(word in lowered for word in patterns):
                return Correction("visit_type", candidate, _spoken("visit_type", candidate, language), lowered)

    # 8. Bare date, e.g. "November 22". Require a month name or slash/dash
    #    numeric form so decimals such as "2.8" cannot be misread as a date.
    if not is_negative(cleaned) and (
        _MONTH_HINT.search(lowered) or _DATE_NUMERIC_HINT.search(lowered)
    ):
        parsed_date = parse_date(normalised, today=today)
        if parsed_date and len(normalised.split()) <= 6:
            iso = parsed_date.value.isoformat()
            return Correction("next_visit_date", iso, _spoken("next_visit_date", iso, language), parsed_date.text)

    return None


def _bool_from_text(lowered: str) -> bool | None:
    if re.search(r"not|no |नहीं|இல்ல|pending|பாக்கி", lowered):
        return False
    if re.search(r"yes|done|completed|given|provided|முடிந்த|கொடுத்த|हो गया|पूरी|दी", lowered):
        return True
    return None


def looks_like_echo(transcript: str, spoken: str) -> bool:
    """Guard against the microphone transcribing our own TTS read-back."""
    left = fold(transcript)
    right = fold(spoken)
    if not left or not right:
        return False
    return SequenceMatcher(None, left, right).ratio() > 0.82
