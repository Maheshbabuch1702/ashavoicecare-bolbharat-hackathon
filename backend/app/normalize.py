"""Text normalisation for code-mixed Indian-language ASR output.

The speech recogniser returns Tamil/Hindi in native script mixed with Latin
medical terms, digits and English words. Everything downstream (field
extraction, danger-sign rules) works on the output of `normalise()`.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta

from .i18n import MONTHS

# --------------------------------------------------------------------------- #
# ASR artefact repair
# --------------------------------------------------------------------------- #

# Verified against real Gnani output: "beneficiary ID ASHAH 102" / "ASHAE102".
_BENEFICIARY_RE = re.compile(r"\bA\s*S\s*H\s*A\s*[A-Z]?\s*[-–]?\s*(\d{2,6})\b", re.IGNORECASE)

# Canonical -> ASR variants seen in practice. Keys are matched case-insensitively.
MEDICAL_ALIASES: dict[str, tuple[str, ...]] = {
    "ANC": ("a n c", "aanc", "ancc", "antenatal", "ante natal", "hence he"),
    "IFA": ("i f a", "ifa tablet", "ifa tablets", "tifa", "ifa goli", "ifa matra"),
    "TT": ("t t", "tetanus", "tt injection", "t.t"),
    "HBNC": ("h b n c", "home based newborn care"),
    "PHC": ("p h c", "primary health centre", "primary health center"),
    "BP": ("b p", "blood pressure"),
    "Hb": ("h b", "hemoglobin", "haemoglobin"),
}


def fold(text: str) -> str:
    """Lowercase, unicode-normalise and collapse whitespace."""
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("\u200b", " ").replace("\u200c", "").replace("\u200d", "")
    text = text.lower()
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    return text.strip()


def levenshtein(a: str, b: str, limit: int = 3) -> int:
    if abs(len(a) - len(b)) > limit:
        return limit + 1
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + (ca != cb),
            ))
        previous = current
    return previous[-1]


def canonicalise_medical_terms(text: str) -> str:
    """Rewrite ASR variants of clinical vocabulary to canonical tokens."""
    result = text
    for canonical, variants in MEDICAL_ALIASES.items():
        for variant in variants:
            pattern = re.compile(rf"(?<!\w){re.escape(variant)}(?!\w)", re.IGNORECASE)
            result = pattern.sub(canonical, result)

    # Fuzzy pass for single-token Latin words: "tifa" -> "IFA", "anc" stays.
    known = ["ANC", "IFA", "HBNC", "PHC", "vaccination", "immunization", "hemoglobin"]
    tokens = re.split(r"(\W+)", result)
    for index, token in enumerate(tokens):
        if len(token) < 4 or not re.fullmatch(r"[A-Za-z]+", token):
            continue
        upper = token.upper()
        for candidate in known:
            if upper == candidate.upper():
                break
            budget = 1 if len(candidate) <= 4 else 2
            if levenshtein(upper, candidate.upper(), limit=budget) <= budget:
                tokens[index] = candidate
                break
    return "".join(tokens)


def canonicalise_beneficiary_ids(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return f"ASHA{match.group(1)}"

    return _BENEFICIARY_RE.sub(replace, text)


# --------------------------------------------------------------------------- #
# Number words
# --------------------------------------------------------------------------- #

_EN_UNITS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19,
}
_EN_TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}
_EN_SCALES = {"hundred": 100, "thousand": 1000}

# Best-effort exact matches for Indic numerals. Digits are what the recogniser
# normally returns (format=transcribe), so this is a safety net rather than the
# main path.
_INDIC_NUMBERS: dict[str, int] = {
    # tamil
    "ஒன்று": 1, "இரண்டு": 2, "மூன்று": 3, "நான்கு": 4, "ஐந்து": 5, "ஆறு": 6,
    "ஏழு": 7, "எட்டு": 8, "ஒன்பது": 9, "பத்து": 10, "இருபது": 20, "முப்பது": 30,
    "நாற்பது": 40, "ஐம்பது": 50, "அறுபது": 60, "எழுபது": 70, "எண்பது": 80,
    "தொண்ணூறு": 90, "நூறு": 100,
    # hindi
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6,
    "सात": 7, "आठ": 8, "नौ": 9, "दस": 10, "बीस": 20, "तीस": 30, "चालीस": 40,
    "पचास": 50, "साठ": 60, "सत्तर": 70, "अस्सी": 80, "नब्बे": 90, "सौ": 100,
    # telugu
    "ఒకటి": 1, "రెండు": 2, "మూడు": 3, "నాలుగు": 4, "ఐదు": 5, "ఆరు": 6,
    "ఏడు": 7, "ఎనిమిది": 8, "తొమ్మిది": 9, "పది": 10,
}

_NUMBER_TOKEN = "|".join(
    sorted(
        [*_EN_UNITS, *_EN_TENS, *_EN_SCALES, "and", "point", *_INDIC_NUMBERS],
        key=len,
        reverse=True,
    )
)

# Match a whole run ("fifty five", "one hundred and twenty") rather than single
# words, otherwise "fifty five" becomes "50 5".
_NUMBER_RUN = re.compile(
    rf"(?<!\w)(?:(?:{_NUMBER_TOKEN})(?:\s+(?:{_NUMBER_TOKEN}))*)(?!\w)",
    re.IGNORECASE,
)


def _parse_english_number(words: list[str]) -> float | None:
    total = 0
    current = 0
    decimal: list[str] = []
    in_decimal = False
    seen = False

    for word in words:
        word = word.lower()
        if word == "and":
            continue
        if word == "point":
            in_decimal = True
            continue
        if word in _EN_UNITS:
            value = _EN_UNITS[word]
        elif word in _EN_TENS:
            value = _EN_TENS[word]
        elif word in _EN_SCALES:
            scale = _EN_SCALES[word]
            current = max(current, 1) * scale
            seen = True
            continue
        else:
            continue
        seen = True
        if in_decimal:
            decimal.append(str(value))
        else:
            current += value

    if not seen:
        return None
    total += current
    if decimal:
        return float(f"{total}.{''.join(decimal)}")
    return float(total)


def number_words_to_digits(text: str) -> str:
    """Replace runs of English/Indic number words with digits."""
    def replace(match: re.Match[str]) -> str:
        span = match.group(0)
        words = span.split()
        if not words:
            return span
        indic = [_INDIC_NUMBERS[w] for w in words if w in _INDIC_NUMBERS]
        if len(indic) == len(words) and indic:
            return str(sum(indic))
        if all(word in {"and", "point"} for word in words):
            return span
        value = _parse_english_number(words)
        if value is None:
            return span
        return str(int(value)) if value == int(value) else f"{value}"

    # Two passes so number runs that appear after a first substitution settle.
    for _ in range(2):
        text = _NUMBER_RUN.sub(replace, text)
    return text


# --------------------------------------------------------------------------- #
# Dates
# --------------------------------------------------------------------------- #

_DATE_NUMERIC = re.compile(
    r"(?<!\d)(\d{1,2})\s*([/\-.])\s*(\d{1,2})(?:\s*[/\-.]\s*(\d{2,4}))?(?!\d)"
)
_MONTH_NAMES = "|".join(sorted((m for m in MONTHS if len(m) > 2), key=len, reverse=True))
_DATE_DAY_FIRST = re.compile(rf"(?<!\d)(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH_NAMES})(?:\s+(\d{{4}}))?", re.IGNORECASE)
_DATE_MONTH_FIRST = re.compile(rf"({_MONTH_NAMES})\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,?\s*(\d{{4}}))?", re.IGNORECASE)


@dataclass(frozen=True)
class ParsedDate:
    value: date
    text: str


def _build_date(day: int, month: int, year: int | None, today: date) -> date | None:
    if not 1 <= day <= 31 or not 1 <= month <= 12:
        return None
    year = year or today.year
    if year < 100:
        year += 2000
    try:
        candidate = date(year, month, day)
    except ValueError:
        return None
    # A next-visit date that is already more than a week past almost certainly
    # means next year (e.g. "November 1" said on 15 November).
    if year == today.year and candidate < today - timedelta(days=7):
        try:
            candidate = date(year + 1, month, day)
        except ValueError:
            return None
    return candidate


def parse_date(text: str, today: date | None = None) -> ParsedDate | None:
    today = today or date.today()
    lowered = fold(text)

    for match in _DATE_MONTH_FIRST.finditer(lowered):
        month = MONTHS.get(fold(match.group(1)))
        day = int(match.group(2))
        year = int(match.group(3)) if match.group(3) else None
        built = _build_date(day, month or 0, year, today)
        if built:
            return ParsedDate(built, match.group(0))

    for match in _DATE_DAY_FIRST.finditer(lowered):
        day = int(match.group(1))
        month = MONTHS.get(fold(match.group(2)))
        year = int(match.group(3)) if match.group(3) else None
        built = _build_date(day, month or 0, year, today)
        if built:
            return ParsedDate(built, match.group(0))

    for match in _DATE_NUMERIC.finditer(lowered):
        separator = match.group(2)
        # A two-part dotted number is a decimal ("weight 2.8 kilo"), not a
        # date. Dotted dates are only accepted with an explicit year.
        if separator == "." and not match.group(4):
            continue
        day, month = int(match.group(1)), int(match.group(3))
        year = int(match.group(4)) if match.group(4) else None
        if year is not None and year < 100:
            year += 2000
        built = _build_date(day, month, year, today)
        if built:
            return ParsedDate(built, match.group(0))

    return None


# --------------------------------------------------------------------------- #
# Weight & vitals
# --------------------------------------------------------------------------- #

_WEIGHT_UNIT = r"(?:kg|kgs|kilo|kilos|kilogram|kilograms|கிலோ|கி\.கி|किलो|కిలో)"
_WEIGHT_NUM = r"(\d{1,3}(?:\.\d{1,2})?)"

_WEIGHT_WITH_UNIT = re.compile(rf"(?<!\d){_WEIGHT_NUM}\s*{_WEIGHT_UNIT}", re.IGNORECASE)
_WEIGHT_AFTER_KEYWORD = re.compile(
    r"(?:weight|wt|எடை|वज़न|वजन|బరువు)[^\d]{0,14}(\d{1,3}(?:\.\d{1,2})?)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedWeight:
    kg: float
    text: str


def parse_weight(text: str) -> ParsedWeight | None:
    match = _WEIGHT_WITH_UNIT.search(text) or _WEIGHT_AFTER_KEYWORD.search(text)
    if not match:
        return None
    try:
        value = float(match.group(1))
    except (TypeError, ValueError):
        return None
    if not 0.5 <= value <= 250:
        return None
    return ParsedWeight(value, match.group(0))


_BP_RE = re.compile(r"(?<!\d)(\d{2,3})\s*(?:/|by|over)\s*(\d{2,3})(?!\d)")


def parse_bp(text: str) -> tuple[int, int] | None:
    match = _BP_RE.search(text)
    if not match:
        return None
    systolic, diastolic = int(match.group(1)), int(match.group(2))
    if 60 <= systolic <= 260 and 30 <= diastolic <= 160 and systolic > diastolic:
        return systolic, diastolic
    return None


# --------------------------------------------------------------------------- #
# Intent helpers
# --------------------------------------------------------------------------- #

_AFFIRMATIVE = (
    "yes", "yeah", "yep", "correct", "right", "ok", "okay", "save", "sure",
    "confirm", "sari", "seri", "aama", "aam", "haan", "ha", "theek", "sahi",
    "சரி", "ஆமா", "ஆம்", "சரியானது", "ठीक", "हाँ", "हां", "सही", "बिल्कुल",
)
_NEGATIVE = (
    "no", "nope", "not correct", "incorrect", "wrong", "change", "illa", "illai",
    "இல்லை", "இல்ல", "தவறு", "nahi", "नहीं", "गलत", "बदलो",
)


def is_affirmative(text: str) -> bool:
    lowered = fold(text)
    if any(fold(word) in lowered for word in _NEGATIVE):
        return False
    return any(re.search(rf"(?<!\w){re.escape(fold(w))}(?!\w)", lowered) for w in _AFFIRMATIVE)


def is_negative(text: str) -> bool:
    lowered = fold(text)
    return any(re.search(rf"(?<!\w){re.escape(fold(w))}(?!\w)", lowered) for w in _NEGATIVE)


_POSITIVE_STATUS = ("completed", "complete", "done", "given", "provided", "yes", "taken", "received")
_NEGATIVE_STATUS = ("not", "no", "pending", "not done", "not given", "didn't", "did not", "missing")


def status_tristate(fragment: str) -> bool | None:
    """Turn 'completed' / 'not done' / '' into True / False / None."""
    lowered = fold(fragment)
    if not lowered:
        return None
    if any(word in lowered for word in _NEGATIVE_STATUS):
        return False
    if any(word in lowered for word in _POSITIVE_STATUS):
        return True
    return None


def normalise(text: str) -> str:
    """Full normalisation pipeline used before extraction and danger matching."""
    text = fold(text)
    text = canonicalise_beneficiary_ids(text)
    text = canonicalise_medical_terms(text)
    text = number_words_to_digits(text)
    return text
