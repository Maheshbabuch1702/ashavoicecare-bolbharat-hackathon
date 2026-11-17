"""Convert a free-text visit note into a structured visit record.

Two extractors are available:

* `extract_rules`  - deterministic, offline, no API key, cannot hallucinate.
* `extract_llm`    - optional OpenAI-compatible structured-output call.

`extract()` prefers the LLM when configured, then validates every field and
falls back to rules. Missing data is left as None and surfaced as a question —
the extractor never invents values.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

import httpx

from .config import Settings
from .normalize import (
    fold,
    normalise,
    parse_bp,
    parse_date,
    parse_weight,
    status_tristate,
)

CRITICAL_FIELDS = ("beneficiary_id", "patient_name", "visit_type", "weight_kg", "next_visit_date")

_NAME_STOPWORDS = {
    "patient", "beneficiary", "name", "id", "asha", "weight", "pregnancy", "visit",
    "newborn", "baby", "anc", "ifa", "next", "today", "mother", "the", "she", "her",
    "checkup", "check", "general", "postnatal", "immunization", "vaccination",
    "நோயாளி", "பெயர்", "பயனாளி", "எடை", "கர்ப்ப", "பரிசோதனை", "வருகை", "குழந்தை",
    "மாத்திரை", "தடுப்பூசி",
    "मरीज़", "नाम", "लाभार्थी", "वज़न", "वजन", "जाँच", "जांच", "विज़िट", "गर्भावस्था",
    "टीकाकरण", "नवजात", "शिशु",
}

_LATIN_NAME = r"[A-Z][a-zA-Z'’]{1,}(?:\s+[A-Z][a-zA-Z'’]{1,})?"
_TAMIL_NAME = r"[\u0B80-\u0BFF]{2,}(?:\s+[\u0B80-\u0BFF]{2,})?"
_HINDI_NAME = r"[\u0900-\u097F]{2,}(?:\s+[\u0900-\u097F]{2,})?"

_NAME_PATTERNS = (
    re.compile(rf"(?:patient|beneficiary)\s*(?:name)?\s*(?:is)?\s*[:\-]?\s*({_LATIN_NAME})"),
    re.compile(rf"\bname\s*(?:is)?\s*[:\-]?\s*({_LATIN_NAME})"),
    re.compile(rf"(?:நோயாளி|பெயர்|பயனாளி)\s*(?:பெயர்)?\s*[:\-]?\s*({_TAMIL_NAME})"),
    re.compile(rf"(?:मरीज़|नाम|लाभार्थी)\s*(?:का नाम)?\s*[:\-]?\s*({_HINDI_NAME})"),
)

# "Lakshmi, beneficiary ID ASHA102" -> the note usually opens with the name.
_LEADING_NAME = re.compile(rf"^\s*({_LATIN_NAME}|{_TAMIL_NAME}|{_HINDI_NAME})\s*[,.]")

_ID_PATTERNS = (
    re.compile(r"\b(ASHA\d{2,6})\b", re.IGNORECASE),
    re.compile(r"(?:beneficiary\s*)?(?:id|ஐடி|आईडी)\s*[:\-]?\s*(\d{3,6})\b", re.IGNORECASE),
)

_VACCINES = {
    "BCG": r"\bbcg\b",
    "OPV": r"\bopv\b|polio",
    "Pentavalent": r"penta(?:valent)?|dpt",
    "MR": r"\bmr\b|measles|rubella",
    "TT": r"\btt\b|tetanus",
    "Hep B": r"hep(?:atitis)?\s?b",
    "Rotavirus": r"rota",
    "PCV": r"\bpcv\b|pneumococcal",
    "IPV": r"\bipv\b",
    "Vitamin A": r"vitamin\s*a\b",
}

# "TT injection given" and "MR vaccine due" must not produce the same record.
# Due is tested first so "not given" is correctly treated as pending.
_VACCINE_DUE = re.compile(
    r"\b(?:due|pending|not given|not done|yet to|remaining|next dose)\b"
    r"|நிலுவை|பாக்கி|கொடுக்கவில்லை|போடவில்லை|இன்னும்"
    r"|बाकी|देना है|नहीं दिया|नहीं दी|नहीं लगा|शेष|अगली खुराक"
)
_VACCINE_GIVEN = re.compile(
    r"\b(?:given|administered|provided|received|done|completed|vaccinated)\b"
    r"|கொடுத்த|வழங்கிய|போட்ட|முடிந்த"
    r"|दिया|दी गई|लगाया|लगा दिया|हो गया|पूरा"
)
_NO_VACCINE_DUE = re.compile(
    r"\b(?:no|not)\b[^.!?]{0,30}\b(?:due|pending)\b"
    r"|தேவை இல்லை|தேவையில்லை"
    r"|बाकी नहीं|नहीं बाकी|ज़रूरत नहीं|जरूरत नहीं"
)

_OBSERVATION_HINTS = (
    "complain", "pain", "advice", "advised", "counsel", "reported", "says", "told",
    "observation", "swelling", "weakness", "dizzy", "vomit", "cough", "cold",
    "புகார்", "வலி", "ஆலோசனை", "शिकायत", "दर्द", "सलाह",
)


@dataclass
class VisitRecord:
    beneficiary_id: str | None = None
    patient_name: str | None = None
    visit_type: str = "general"
    weight_kg: float | None = None
    bp: str | None = None
    anc_completed: bool | None = None
    ifa_provided: bool | None = None
    vaccination_status: str | None = None          # given | due | not_specified
    vaccines_due: list[str] = field(default_factory=list)
    next_visit_date: str | None = None             # ISO date
    observations: str | None = None
    language: str = "en-IN"
    transcript: str = ""
    confidence: dict[str, float] = field(default_factory=dict)
    evidence: dict[str, str] = field(default_factory=dict)
    extraction_method: str = "rules"

    def as_dict(self) -> dict[str, Any]:
        return {
            "beneficiary_id": self.beneficiary_id,
            "patient_name": self.patient_name,
            "visit_type": self.visit_type,
            "weight_kg": self.weight_kg,
            "bp": self.bp,
            "anc_completed": self.anc_completed,
            "ifa_provided": self.ifa_provided,
            "vaccination_status": self.vaccination_status,
            "vaccines_due": self.vaccines_due,
            "next_visit_date": self.next_visit_date,
            "observations": self.observations,
            "language": self.language,
            "transcript": self.transcript,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "extraction_method": self.extraction_method,
        }

    def missing(self) -> list[str]:
        """Fields a health worker must supply before saving."""
        checks: list[str] = ["beneficiary_id", "patient_name"]
        if self.visit_type in {"pregnancy_anc", "newborn_hbnc", "postnatal"}:
            checks.append("weight_kg")
        checks.append("next_visit_date")
        return [name for name in checks if getattr(self, name) in (None, "", [])]

    def low_confidence(self, threshold: float = 0.55) -> list[str]:
        return [
            name
            for name, score in self.confidence.items()
            if score < threshold and getattr(self, name, None) not in (None, "", [])
        ]


# --------------------------------------------------------------------------- #
# rule-based extraction
# --------------------------------------------------------------------------- #

def _valid_name(candidate: str) -> bool:
    candidate = candidate.strip(" ,.-")
    if len(candidate) < 2 or re.search(r"\d", candidate):
        return False
    tokens = re.findall(r"[\w\u0B80-\u0BFF\u0900-\u097F]+", candidate)
    if not tokens:
        return False
    # Rejects "beneficiary ID ASHA" style captures.
    return not any(fold(token) in _NAME_STOPWORDS for token in tokens)


def _grab_name(raw: str, normalised: str) -> tuple[str | None, float, str]:
    for pattern in _NAME_PATTERNS:
        for source in (raw, normalised):
            match = pattern.search(source)
            if match and _valid_name(match.group(1)):
                return match.group(1).strip(" ,.-"), 0.95, match.group(0)

    match = _LEADING_NAME.search(raw)
    if match and _valid_name(match.group(1)):
        return match.group(1).strip(" ,.-"), 0.7, match.group(0)
    return None, 0.0, ""


def _grab_id(text: str) -> tuple[str | None, float, str]:
    match = _ID_PATTERNS[0].search(text)
    if match:
        return match.group(1).upper(), 0.97, match.group(0)
    match = _ID_PATTERNS[1].search(text)
    if match:
        return match.group(1), 0.7, match.group(0)
    return None, 0.0, ""


def _grab_visit_type(lowered: str) -> tuple[str, float, str]:
    ordered = (
        ("pregnancy_anc", (
            r"pregnancy visit", r"anc visit", r"antenatal", r"\banc\b", r"pregnancy",
            r"pregnant", r"கர்ப்ப", r"गर्भवती", r"गर्भावस्था",
        )),
        ("newborn_hbnc", (
            r"newborn", r"new born", r"\bhbnc\b", r"\bbaby\b", r"infant",
            r"கைக்குழந்தை", r"புதிதாகப் பிறந்த", r"नवजात", r"शिशु",
        )),
        ("postnatal", (
            r"postnatal", r"post natal", r"after delivery", r"after birth",
            r"பிரசவத்திற்குப் பின்", r"प्रसव के बाद",
        )),
        ("immunization", (
            r"immuni[sz]ation", r"vaccination visit", r"vaccine", r"தடுப்பூசி", r"टीकाकरण", r"टीका",
        )),
        ("family_planning", (
            r"family planning", r"contracept", r"குடும்பக் கட்டுப்பாடு", r"परिवार नियोजन",
        )),
    )
    for visit_type, patterns in ordered:
        for pattern in patterns:
            match = re.search(pattern, lowered)
            if match:
                return visit_type, 0.9 if visit_type != "pregnancy_anc" else 0.92, match.group(0)

    # A note that only says "visit completed"/"home visit" is a general visit.
    if re.search(r"home visit|visit completed|வருகை|विज़िट", lowered):
        return "general", 0.5, "visit completed"
    return "general", 0.3, ""


def _grab_tristate(
    lowered: str,
    positive_patterns: tuple[str, ...],
    negative_patterns: tuple[str, ...],
) -> tuple[bool | None, float, str]:
    for pattern in negative_patterns:
        match = re.search(pattern, lowered)
        if match:
            return False, 0.9, match.group(0)
    for pattern in positive_patterns:
        match = re.search(pattern, lowered)
        if match:
            return True, 0.9, match.group(0)
    return None, 0.0, ""


def extract_rules(
    transcript: str,
    *,
    language: str = "en-IN",
    today=None,
) -> VisitRecord:
    raw = transcript or ""
    normalised = normalise(raw)
    lowered = fold(normalised)

    record = VisitRecord(language=language, transcript=raw, extraction_method="rules")

    name, name_conf, name_evidence = _grab_name(raw, normalised)
    if name:
        record.patient_name = name
        record.confidence["patient_name"] = name_conf
        record.evidence["patient_name"] = name_evidence

    beneficiary_id, id_conf, id_evidence = _grab_id(normalised)
    if beneficiary_id:
        record.beneficiary_id = beneficiary_id
        record.confidence["beneficiary_id"] = id_conf
        record.evidence["beneficiary_id"] = id_evidence

    visit_type, type_conf, type_evidence = _grab_visit_type(lowered)
    record.visit_type = visit_type
    record.confidence["visit_type"] = type_conf
    if type_evidence:
        record.evidence["visit_type"] = type_evidence

    weight = parse_weight(normalised)
    if weight:
        plausible = (0.5 <= weight.kg <= 12) if visit_type == "newborn_hbnc" else (20 <= weight.kg <= 200)
        record.weight_kg = weight.kg
        record.confidence["weight_kg"] = 0.95 if plausible else 0.3
        record.evidence["weight_kg"] = weight.text

    bp = parse_bp(normalised)
    if bp:
        record.bp = f"{bp[0]}/{bp[1]}"

    # Real ASR confusion: "ANC completed" comes back as "HBNC completed".
    # HBNC is a newborn-programme term, so it cannot mean an ANC field inside a
    # pregnancy note; repair only in that context.
    anc_lowered = lowered
    if visit_type == "pregnancy_anc":
        anc_lowered = re.sub(r"\bhbnc\b", "anc", anc_lowered)

    anc, anc_conf, anc_evidence = _grab_tristate(
        anc_lowered,
        positive_patterns=(
            r"anc (?:checkup )?(?:is )?(?:completed|done|normal|ok)",
            r"anc (?:பரிசோதனை )?முடிந்த",
            r"பரிசோதனை முடிந்த",
            r"anc (?:जाँच )?(?:पूरी|हो गई)",
            r"जाँच पूरी",
            r"(?:checkup|check up) (?:is )?completed",
        ),
        negative_patterns=(
            r"anc (?:checkup )?(?:not|pending|incomplete)",
            r"anc (?:பரிசோதனை )?முடிக்கவில்லை",
            r"anc (?:जाँच )?(?:नहीं|बाकी)",
        ),
    )
    if anc is not None:
        record.anc_completed = anc
        record.confidence["anc_completed"] = anc_conf
        record.evidence["anc_completed"] = anc_evidence
    elif visit_type == "pregnancy_anc" and re.search(r"checkup|check up|பரிசோதனை|जाँच", anc_lowered):
        record.anc_completed = status_tristate(anc_lowered)
        if record.anc_completed is not None:
            record.confidence["anc_completed"] = 0.55
            record.evidence["anc_completed"] = "checkup status"

    ifa, ifa_conf, ifa_evidence = _grab_tristate(
        lowered,
        positive_patterns=(
            r"ifa (?:tablets?|goli|மாத்திரை)?\s*(?:is |was |were )?(?:given|provided|issued)",
            r"ifa (?:மாத்திரை )?கொடுத்த",
            r"ifa (?:टैबलेट )?(?:दी|दिया)",
            r"(?:gave|provided) ifa",
        ),
        negative_patterns=(
            r"ifa (?:tablets?|goli)?\s*(?:not|नहीं)",
            r"no ifa",
            r"ifa (?:மாத்திரை )?(?:கொடுக்கவில்லை|இல்லை)",
            r"ifa (?:टैबलेट )?नहीं (?:दी|दिया)",
        ),
    )
    if ifa is not None:
        record.ifa_provided = ifa
        record.confidence["ifa_provided"] = ifa_conf
        record.evidence["ifa_provided"] = ifa_evidence

    vaccine_names = [name for name, pattern in _VACCINES.items() if re.search(pattern, lowered)]
    if vaccine_names:
        due_names: list[str] = []
        given_names: list[str] = []
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", raw):
            folded_sentence = fold(sentence)
            names = [
                name
                for name, pattern in _VACCINES.items()
                if re.search(pattern, folded_sentence)
            ]
            if not names:
                continue
            if _NO_VACCINE_DUE.search(folded_sentence):
                continue
            if _VACCINE_DUE.search(folded_sentence):
                due_names.extend(name for name in names if name not in due_names)
            elif _VACCINE_GIVEN.search(folded_sentence):
                given_names.extend(name for name in names if name not in given_names)

        if due_names:
            record.vaccination_status = "due"
            record.vaccines_due = due_names
            record.confidence["vaccination_status"] = 0.9
            record.evidence["vaccination_status"] = "due: " + ", ".join(due_names)
        elif given_names:
            record.vaccination_status = "given"
            record.vaccines_due = []
            record.confidence["vaccination_status"] = 0.9
            record.evidence["vaccination_status"] = "given: " + ", ".join(given_names)
        else:
            # A bare vaccine name does not prove the dose was given or is due.
            # Never invent either status; ask the worker to confirm it.
            record.vaccination_status = "not_specified"
            record.vaccines_due = []
            record.confidence["vaccination_status"] = 0.35
            record.evidence["vaccination_status"] = "mentioned: " + ", ".join(vaccine_names)
    elif re.search(r"vaccin|immuni[sz]|தடுப்பூசி|टीकाकरण|टीका", lowered):
        record.vaccination_status = "due"
        record.confidence["vaccination_status"] = 0.8
        record.evidence["vaccination_status"] = "vaccination mentioned without doses"
    elif re.search(r"vaccin\w*\s+(?:is )?(?:pending|due)|not (?:given|done)", lowered):
        record.vaccination_status = "due"
        record.confidence["vaccination_status"] = 0.8

    parsed_date = parse_date(normalised, today=today)
    if parsed_date:
        record.next_visit_date = parsed_date.value.isoformat()
        has_context = bool(re.search(r"next visit|அடுத்த வருகை|अगली विज़िट|next|அடுத்த", lowered))
        record.confidence["next_visit_date"] = 0.95 if has_context else 0.7
        record.evidence["next_visit_date"] = parsed_date.text

    sentences = re.split(r"(?<=[.!?])\s+|\n+", raw)
    observations = [
        sentence.strip()
        for sentence in sentences
        if sentence.strip() and any(hint in fold(sentence) for hint in _OBSERVATION_HINTS)
    ]
    if observations:
        record.observations = " ".join(observations)[:400]

    return record


# --------------------------------------------------------------------------- #
# optional LLM extraction
# --------------------------------------------------------------------------- #

_LLM_SYSTEM = """You extract structured visit data for an ASHA (community health worker) record.
Return ONLY JSON matching the schema. Rules:
- Never invent values. If a field was not spoken, return null.
- Copy numbers exactly as spoken; do not round or infer.
- Do not diagnose, do not suggest medicine or treatment.
- visit_type must be one of: pregnancy_anc, newborn_hbnc, postnatal, immunization, family_planning, general.
- next_visit_date must be ISO YYYY-MM-DD when a date is spoken, else null."""

_LLM_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "beneficiary_id": {"type": ["string", "null"]},
        "patient_name": {"type": ["string", "null"]},
        "visit_type": {"type": "string"},
        "weight_kg": {"type": ["number", "null"]},
        "bp": {"type": ["string", "null"]},
        "anc_completed": {"type": ["boolean", "null"]},
        "ifa_provided": {"type": ["boolean", "null"]},
        "vaccination_status": {"type": ["string", "null"]},
        "vaccines_due": {"type": "array", "items": {"type": "string"}},
        "next_visit_date": {"type": ["string", "null"]},
        "observations": {"type": ["string", "null"]},
    },
    "required": ["visit_type"],
}


def extract_llm(transcript: str, *, language: str, settings: Settings, today=None) -> VisitRecord | None:
    if not settings.llm_ready:
        return None
    payload = {
        "model": settings.llm_model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": _LLM_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Language: {language}\nToday: {today.isoformat() if today else 'unknown'}\n"
                    f"Transcript:\n{transcript}"
                ),
            },
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "visit_record", "schema": _LLM_SCHEMA, "strict": True},
        },
    }
    try:
        response = httpx.post(
            f"{settings.llm_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            json=payload,
            timeout=25.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
    except Exception:  # noqa: BLE001 - any LLM failure falls back to rules
        return None

    record = VisitRecord(language=language, transcript=transcript, extraction_method="llm")
    for key in (
        "beneficiary_id", "patient_name", "weight_kg", "bp", "anc_completed",
        "ifa_provided", "vaccination_status", "next_visit_date", "observations",
    ):
        if key in data:
            setattr(record, key, data[key])
    if data.get("visit_type") in {
        "pregnancy_anc", "newborn_hbnc", "postnatal", "immunization", "family_planning", "general"
    }:
        record.visit_type = data["visit_type"]
    record.vaccines_due = [str(v) for v in data.get("vaccines_due") or []]
    for key in ("beneficiary_id", "patient_name", "weight_kg", "next_visit_date", "visit_type"):
        record.confidence[key] = 0.85
    return record


def extract(
    transcript: str,
    *,
    language: str = "en-IN",
    settings: Settings | None = None,
    today=None,
) -> VisitRecord:
    """Extract a record, preferring the LLM but always validating with rules."""
    rules_record = extract_rules(transcript, language=language, today=today)
    if settings and settings.llm_ready:
        llm_record = extract_llm(transcript, language=language, settings=settings, today=today)
        if llm_record:
            # Keep rule-based evidence for fields the LLM left empty.
            for key, value in rules_record.as_dict().items():
                if key in {"transcript", "language", "confidence", "evidence", "extraction_method"}:
                    continue
                if getattr(llm_record, key, None) in (None, "", []):
                    setattr(llm_record, key, value)
            llm_record.extraction_method = "llm+rules"
            return llm_record
    return rules_record
