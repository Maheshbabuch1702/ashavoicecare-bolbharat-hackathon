"""Danger-sign rule engine.

This module is deliberately independent of the LLM extractor. It is a fixed,
guideline-derived rule set with explicit negation handling, so a hallucinating
language model can never invent — or silently drop — an emergency.

Guideline sources (see README for full citation block):
  G1  MoHFW, Guidelines for Antenatal Care and Skilled Attendance at Birth
      by ANMs/LHVs/SNs, 2010 — danger-sign checklist, pregnancy
  G2  MoHFW/NHSRC, Home Based Newborn Care Operational Guide, 2014 — newborn
      danger signs and referral
  G3  MoHFW, ASHA Module 6 "Skills that Save Lives" — recognition & referral

The engine does NOT diagnose. It maps recognised phrases to a fixed list and
returns a referral instruction.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Literal

from .normalize import fold, normalise

Subject = Literal["newborn", "mother", "any"]


@dataclass(frozen=True)
class DangerRule:
    code: str
    subject: Subject
    label_en: str
    label_ta: str
    label_hi: str
    patterns: tuple[str, ...]
    source: str
    urgency: str = "emergency"


RULES: tuple[DangerRule, ...] = (
    # ------------------------------- pregnancy ------------------------------ #
    DangerRule(
        code="vaginal_bleeding",
        subject="mother",
        label_en="Vaginal bleeding",
        label_ta="பிறப்புறுப்பு இரத்தப்போக்கு",
        label_hi="योनि से रक्तस्राव",
        patterns=(
            r"heavy bleeding", r"bleeding during pregnancy", r"bleeding from (?:the )?(?:vagina|vaginal)",
            r"vaginal bleeding", r"(?:she is|is) bleeding", r"\bbleeding\b",
            r"இரத்தப்போக்கு", r"ரத்தம் போகிறது", r"இரத்தம் வருகிறது",
            r"खून बह", r"रक्तस्राव", r"ब्लीडिंग",
        ),
        source="G1 §Danger signs during pregnancy; G3",
    ),
    DangerRule(
        code="severe_headache",
        subject="mother",
        label_en="Severe headache or blurred vision",
        label_ta="கடுமையான தலைவலி அல்லது மங்கலான பார்வை",
        label_hi="तेज़ सिरदर्द या धुंधला दिखना",
        patterns=(
            r"severe headache", r"bad headache", r"blurred vision", r"blurring of vision",
            r"கடுமையான தலைவலி", r"பார்வை மங்க",
            r"तेज़ सिरदर्द", r"तेज सिरदर्द", r"धुंधला दिख",
        ),
        source="G1 §Danger signs during pregnancy",
    ),
    DangerRule(
        code="convulsions",
        subject="any",
        label_en="Convulsions / fits",
        label_ta="வலிப்பு",
        label_hi="दौरे / झटके",
        patterns=(
            r"convulsion", r"seizure", r"\bfits\b", r"fainting", r"unconscious",
            r"வலிப்பு", r"மயக்கம்", r"दौरा", r"मिर्गी", r"बेहोश",
        ),
        source="G1; G2",
    ),
    DangerRule(
        code="high_fever",
        subject="any",
        label_en="High fever",
        label_ta="அதிக காய்ச்சல்",
        label_hi="तेज़ बुखार",
        patterns=(
            r"high fever", r"very high fever", r"fever (?:is )?(?:high|104|103)",
            r"(?:temperature|temp) (?:is )?(?:10[3-9]|4[0-2])",
            r"அதிக காய்ச்சல்", r"காய்ச்சல்", r"तेज़ बुखार", r"तेज बुखार", r"बुखार",
        ),
        source="G1; G2",
    ),
    DangerRule(
        code="reduced_fetal_movement",
        subject="mother",
        label_en="Reduced or absent baby movement",
        label_ta="குழந்தையின் அசைவு குறைவு",
        label_hi="शिशु की हलचल कम या बंद",
        patterns=(
            r"(?:baby|fetus|foetus) (?:is )?not moving", r"reduced (?:fetal )?movement",
            r"no (?:baby )?movement", r"குழந்தை அசைவு இல்ல", r"அசைவு குறை",
            r"हलचल (?:कम|नहीं)", r"बच्चा हिल नहीं",
        ),
        source="G1 §Danger signs during pregnancy",
    ),
    DangerRule(
        code="swelling",
        subject="mother",
        label_en="Swelling of face or hands",
        label_ta="முகம் அல்லது கைகளில் வீக்கம்",
        label_hi="चेहरे या हाथों में सूजन",
        patterns=(
            r"swelling of (?:the )?(?:face|hands|feet)", r"face is swollen", r"hands are swollen",
            r"pedal edema", r"முகம் வீங்க", r"கை வீங்க", r"सूजन", r"चेहरा सूज",
        ),
        source="G1 §Danger signs during pregnancy",
    ),
    DangerRule(
        code="leaking_fluid",
        subject="mother",
        label_en="Leaking of fluid",
        label_ta="நீர் இறங்குதல்",
        label_hi="पानी का रिसाव",
        patterns=(
            r"water broke", r"leaking (?:of )?(?:fluid|water)", r"fluid leak",
            r"நீர் இறங்க", r"தண்ணீர் போக", r"पानी (?:की थैली )?(?:फट|रिस)",
        ),
        source="G1 §Danger signs during pregnancy",
    ),
    DangerRule(
        code="severe_abdominal_pain",
        subject="mother",
        label_en="Severe abdominal pain",
        label_ta="கடுமையான வயிற்று வலி",
        label_hi="तेज़ पेट दर्द",
        patterns=(
            r"severe (?:abdominal|stomach) pain", r"severe pain in (?:the )?(?:abdomen|stomach)",
            r"கடுமையான வயிற்று வலி", r"तेज़ पेट दर्द", r"तेज पेट दर्द",
        ),
        source="G1 §Danger signs during pregnancy",
    ),
    DangerRule(
        code="difficulty_breathing",
        subject="any",
        label_en="Difficulty in breathing",
        label_ta="மூச்சுத் திணறல்",
        label_hi="साँस लेने में कठिनाई",
        patterns=(
            r"difficulty (?:in )?breathing", r"breathless", r"shortness of breath",
            r"மூச்சுத் திணற", r"மூச்சு விட சிரமம்", r"साँस लेने में", r"सांस फूल",
        ),
        source="G1; G2",
    ),
    # -------------------------------- newborn ------------------------------- #
    DangerRule(
        code="newborn_not_feeding",
        subject="newborn",
        label_en="Not feeding / feeding poorly",
        label_ta="பாலூட்ட மறுக்கிறது / சரியாக பால் குடிக்கவில்லை",
        label_hi="दूध नहीं पी रहा / कम पी रहा",
        patterns=(
            r"(?:not|barely|poorly) feeding", r"refus(?:es|ing) (?:to )?(?:feed|breastfeed)",
            r"not (?:taking )?(?:breast )?milk", r"பால் குடிக்கவில்லை", r"பால் உண்ணவில்லை",
            r"दूध नहीं पी", r"दूध कम पी",
        ),
        source="G2 §Newborn danger signs",
    ),
    DangerRule(
        code="newborn_low_temperature",
        subject="newborn",
        label_en="Low body temperature",
        label_ta="உடல் வெப்பநிலை குறைவு",
        label_hi="शरीर का तापमान कम",
        patterns=(
            r"body (?:is )?(?:cold|very cold|cool|cooling)", r"cold to touch",
            r"hypothermia", r"(?:baby|newborn) (?:is )?(?:very )?cold",
            r"உடல் குளிர", r"குளிர்ந்து போன",
            r"शरीर ठंडा", r"हाइपोथर्मिया",
        ),
        source="G2 §Newborn danger signs",
    ),
    DangerRule(
        code="newborn_fast_breathing",
        subject="newborn",
        label_en="Fast breathing",
        label_ta="வேகமான மூச்சு",
        label_hi="तेज़ साँस",
        patterns=(
            r"fast breathing", r"breathing (?:is )?(?:very )?fast",
            r"breathing (?:is )?rapid", r"(?:60|70|80) (?:breaths|per minute)",
            r"வேகமாக மூச்சு", r"மூச்சு வேகம்", r"तेज़ साँस", r"तेज सांस",
        ),
        source="G2 §Newborn danger signs",
    ),
    DangerRule(
        code="newborn_chest_indrawing",
        subject="newborn",
        label_en="Chest indrawing",
        label_ta="மார்பு உள்ளிழுத்தல்",
        label_hi="छाती धँसना",
        patterns=(
            r"chest (?:is )?(?:indrawing|indrawn|pulling in|sucking in)",
            r"மார்பு உள்ளிழ", r"छाती (?:धँस|अंदर)",
        ),
        source="G2 §Newborn danger signs",
    ),
    DangerRule(
        code="newborn_jaundice",
        subject="newborn",
        label_en="Jaundice (yellow skin or eyes)",
        label_ta="மஞ்சள் காமாலை",
        label_hi="पीलिया",
        patterns=(
            r"jaundice", r"(?:skin|eyes|body) (?:is |looks )?yellow", r"yellowish",
            r"மஞ்சள்", r"பीलिया", r"पीलिया", r"शरीर पीला",
        ),
        source="G2 §Newborn danger signs",
    ),
    DangerRule(
        code="newborn_umbilical_infection",
        subject="newborn",
        label_en="Umbilical redness or pus",
        label_ta="கொப்பூழில் சிவப்பு அல்லது சீழ்",
        label_hi="नाभि में लाली या मवाद",
        patterns=(
            r"(?:pus|discharge) (?:from|in) (?:the )?(?:umbilicus|umbilical|cord)",
            r"(?:umbilicus|cord|navel) (?:is )?(?:red|swollen|infected)",
            r"கொப்பூழ்\S*\s*(?:சிவப்பு|சீழ்|வீக்கம்|தொற்று)",
            r"தொப்புள்\S*\s*(?:சிவப்பு|சீழ்|வீக்கம்|தொற்று)",
            r"नाभि(?:\s*में)?\s*(?:लाली|मवाद|सूजन|संक्रमण)",
        ),
        source="G2 §Newborn danger signs",
    ),
    DangerRule(
        code="newborn_persistent_vomiting",
        subject="newborn",
        label_en="Persistent vomiting / no urine",
        label_ta="தொடர்ந்து வாந்தி / சிறுநீர் இல்லை",
        label_hi="लगातार उल्टी / पेशाब नहीं",
        patterns=(
            r"persistent vomiting", r"vomiting everything", r"not passing urine", r"no urine",
            r"தொடர்ந்து வாந்தி", r"சிறுநீர் இல்லை", r"लगातार उल्टी", r"पेशाब नहीं",
        ),
        source="G2 §Newborn danger signs",
    ),
    # ------------------------------- postpartum ----------------------------- #
    DangerRule(
        code="postpartum_heavy_bleeding",
        subject="mother",
        label_en="Heavy bleeding after delivery",
        label_ta="பிரசவத்திற்குப் பின் அதிக இரத்தப்போக்கு",
        label_hi="प्रसव के बाद अधिक रक्तस्राव",
        patterns=(
            r"heavy bleeding after (?:delivery|birth)", r"bleeding after (?:delivery|birth)",
            r"postpartum h(?:a)?emorrhage", r"பிரசவத்திற்குப் பின் இரத்தம்",
            r"प्रसव के बाद खून",
        ),
        source="G3 §Postpartum danger signs",
    ),
    DangerRule(
        code="postpartum_infection",
        subject="mother",
        label_en="Foul-smelling discharge or fever after delivery",
        label_ta="பிரசவத்திற்குப் பின் துர்நாற்றம் / காய்ச்சல்",
        label_hi="प्रसव के बाद बदबूदार स्राव या बुखार",
        patterns=(
            r"foul (?:smell|smelling|discharge)", r"bad smell (?:from|in)",
            r"fever after (?:delivery|birth)",
            r"துர்நாற்றம்", r"பிரசவத்திற்குப் பின் காய்ச்சல்",
            r"बदबू", r"दुर्गंध", r"प्रसव के बाद बुखार",
        ),
        source="G3 §Postpartum danger signs",
    ),
)


NEWBORN_CUES = (
    "newborn", "new born", "baby", "infant", "neonate", "child", "boy", "girl",
    "குழந்தை", "கைக்குழந்தை", "பிறந்த", "शिशु", "बच्चा", "नवजात", "बच्ची",
)
MOTHER_CUES = (
    "mother", "patient", "woman", "she", "her", "lady", "pregnant", "pregnancy",
    "தாய்", "நோயாளி", "கர்ப்ப", "मरीज़", "महिला", "माँ", "गर्भ",
)

# Negation markers checked in the window immediately before a match.
_PRE_NEGATION = re.compile(
    r"(?<!\w)(?:no|not|nil|none|absent|negative|denies|denied|without|never|"
    r"hasn't|has not|doesn't|does not|didn't|did not|don't|do not|nothing|"
    r"illa|illai|ila|ledu|nahi|nathi)(?!\w)"
    r"|இல்லை|இல்லாமல்|இல்ல|எதுவுமில்லை|இல்லவே இல்லை|नहीं|बिना|कोई नहीं|नहीं है",
    re.IGNORECASE,
)

# ...and in the short window immediately after one ("bleeding illa", "fever नहीं").
_POST_NEGATION = re.compile(
    r"(?<!\w)(?:no|not|nil|negative|absent|illa|illai|ila|ledu|nahi)(?!\w)"
    r"|இல்லை|இல்ல|நில்லை|नहीं|नहीं है",
    re.IGNORECASE,
)

# Explicit all-clear phrases.
_ALL_CLEAR = re.compile(
    r"no danger signs?|no warning signs?|nothing serious|all (?:is )?(?:fine|normal|well)|"
    r"ஆபத்து அறிகுறி (?:இல்லை|எதுவும் இல்லை)|எந்த ஆபத்தும் இல்லை|"
    r"कोई खतरे का संकेत नहीं|सब ठीक है",
    re.IGNORECASE,
)

_CLAUSE_BREAK = re.compile(r"[.,;:!?]|(?<!\w)but(?!\w)|(?<!\w)however(?!\w)|ஆனால்|लेकिन", re.IGNORECASE)


def _subject_from_text(window: str, fallback: str) -> str:
    lowered = fold(window)
    has_newborn = any(cue in lowered for cue in NEWBORN_CUES)
    has_mother = any(cue in lowered for cue in MOTHER_CUES)
    if has_newborn and not has_mother:
        return "newborn"
    if has_mother and not has_newborn:
        return "mother"
    if has_newborn and has_mother:
        # "baby" is the more specific subject in a mixed sentence.
        return "newborn"
    return fallback


def _category_for(subject: str, fallback: str) -> str:
    if subject == "newborn":
        return "newborn"
    return fallback


def _is_negated(text: str, start: int, end: int) -> bool:
    pre = text[max(0, start - 48):start]
    post = text[end:end + 30]

    # Only look inside the current clause.
    breaks = list(_CLAUSE_BREAK.finditer(pre))
    if breaks:
        pre = pre[breaks[-1].end():]
    post = _CLAUSE_BREAK.split(post)[0]

    return bool(_PRE_NEGATION.search(pre) or _POST_NEGATION.search(post))


@dataclass
class DangerHit:
    code: str
    category: str
    label: str
    label_local: str
    matched_text: str
    urgency: str
    source: str
    position: int = 0

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "category": self.category,
            "label": self.label,
            "label_local": self.label_local,
            "matched_text": self.matched_text,
            "urgency": self.urgency,
            "source": self.source,
        }


@dataclass
class DangerResult:
    hits: list[DangerHit] = field(default_factory=list)
    all_clear: bool = False
    checked_rules: int = 0

    @property
    def has_danger(self) -> bool:
        return bool(self.hits)

    @property
    def categories(self) -> list[str]:
        seen: list[str] = []
        for hit in self.hits:
            if hit.category not in seen:
                seen.append(hit.category)
        return seen


def detect(
    text: str,
    *,
    language: str = "en-IN",
    visit_type: str = "pregnancy_anc",
    weight_kg: float | None = None,
    today_iso: str | None = None,
) -> DangerResult:
    """Run the fixed danger-sign list over free text.

    `text` may be a full transcript or a single new segment. Negated mentions
    ("no bleeding", "bleeding illa") never raise an alert.
    """
    normalised = normalise(text)
    lowered = fold(normalised)
    fallback_subject = "newborn" if visit_type == "newborn_hbnc" else "mother"
    fallback_category = "newborn" if visit_type == "newborn_hbnc" else (
        "postpartum" if visit_type == "postnatal" else "pregnancy"
    )

    result = DangerResult(all_clear=bool(_ALL_CLEAR.search(lowered)), checked_rules=len(RULES))
    seen: set[str] = set()

    for rule in RULES:
        for pattern in rule.patterns:
            for match in re.finditer(pattern, lowered, re.IGNORECASE):
                if _is_negated(lowered, match.start(), match.end()):
                    continue
                window = lowered[max(0, match.start() - 70): match.end() + 70]
                subject = _subject_from_text(window, fallback_subject)
                if rule.subject != "any" and rule.subject != subject:
                    continue
                category = _category_for(subject, fallback_category)
                # A postpartum-specific rule only applies to a mother category.
                if rule.code.startswith("postpartum") and category == "pregnancy":
                    category = "postpartum"
                if rule.code in seen:
                    continue
                seen.add(rule.code)
                label_local = {"ta-IN": rule.label_ta, "hi-IN": rule.label_hi}.get(
                    language, rule.label_en
                )
                result.hits.append(
                    DangerHit(
                        code=rule.code,
                        category=category,
                        label=rule.label_en,
                        label_local=label_local,
                        matched_text=match.group(0),
                        urgency=rule.urgency,
                        source=rule.source,
                        position=match.start(),
                    )
                )
                break

    # Numeric rule: low birth weight is a newborn danger sign (G2).
    if weight_kg is not None and weight_kg < 2.5 and fallback_subject == "newborn":
        if "low_birth_weight" not in seen:
            result.hits.append(
                DangerHit(
                    code="low_birth_weight",
                    category="newborn",
                    label="Low birth weight (<2.5 kg)",
                    label_local={
                        "ta-IN": "குறைந்த பிறப்பு எடை (2.5 கிலோவுக்கும் குறைவு)",
                        "hi-IN": "कम जन्म वज़न (2.5 किलो से कम)",
                    }.get(language, "Low birth weight (<2.5 kg)"),
                    matched_text=f"{weight_kg} kg",
                    urgency="urgent",
                    source="G2 §Newborn danger signs",
                )
            )

    result.hits.sort(key=lambda hit: hit.position)
    return result


def diff(new: DangerResult, already: Iterable[str]) -> list[DangerHit]:
    """Return only hits whose code has not been reported yet."""
    known = set(already)
    return [hit for hit in new.hits if hit.code not in known]
