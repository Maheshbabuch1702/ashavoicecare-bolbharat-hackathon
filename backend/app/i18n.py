"""Localised strings for spoken prompts, read-back and danger warnings.

Only three languages are wired for the demo (English, Tamil, Hindi). Adding a
language means adding one entry to LANGUAGES and one block per template dict.
"""

from __future__ import annotations

SUPPORTED_LANGUAGES: dict[str, str] = {
    "en-IN": "English",
    "ta-IN": "Tamil",
    "hi-IN": "Hindi",
}

DEFAULT_LANGUAGE = "en-IN"


def normalise_language(code: str | None) -> str:
    if not code:
        return DEFAULT_LANGUAGE
    code = code.strip()
    if code in SUPPORTED_LANGUAGES:
        return code
    base = code.split("-")[0].lower()
    for known in SUPPORTED_LANGUAGES:
        if known.split("-")[0] == base:
            return known
    return DEFAULT_LANGUAGE


MONTHS: dict[str, int] = {
    # english
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
    # tamil
    "ஜனவரி": 1, "பிப்ரவரி": 2, "மார்ச்": 3, "ஏப்ரல்": 4, "மே": 5, "ஜூன்": 6,
    "ஜூலை": 7, "ஆகஸ்ட்": 8, "செப்டம்பர்": 9, "அக்டோபர்": 10, "நவம்பர்": 11, "டிசம்பர்": 12,
    # hindi
    "जनवरी": 1, "फरवरी": 2, "मार्च": 3, "अप्रैल": 4, "मई": 5, "जून": 6,
    "जुलाई": 7, "अगस्त": 8, "सितंबर": 9, "अक्टूबर": 10, "नवंबर": 11, "दिसंबर": 12,
}

# Canonical visit types. Keys are stored in the database.
VISIT_TYPE_LABELS: dict[str, dict[str, str]] = {
    "pregnancy_anc": {
        "en-IN": "Pregnancy visit (ANC)",
        "ta-IN": "கர்ப்பகால பரிசோதனை வருகை",
        "hi-IN": "गर्भावस्था जाँच (ANC)",
    },
    "newborn_hbnc": {
        "en-IN": "Newborn home visit (HBNC)",
        "ta-IN": "புதிதாகப் பிறந்த குழந்தை வீட்டு வருகை",
        "hi-IN": "नवजात शिशु गृह भेंट",
    },
    "postnatal": {
        "en-IN": "Postnatal visit",
        "ta-IN": "பிரசவத்திற்குப் பின் வருகை",
        "hi-IN": "प्रसव के बाद विज़िट",
    },
    "immunization": {
        "en-IN": "Immunization visit",
        "ta-IN": "தடுப்பூசி வருகை",
        "hi-IN": "टीकाकरण विज़िट",
    },
    "family_planning": {
        "en-IN": "Family planning visit",
        "ta-IN": "குடும்பக் கட்டுப்பாடு வருகை",
        "hi-IN": "परिवार नियोजन विज़िट",
    },
    "general": {
        "en-IN": "General visit",
        "ta-IN": "பொதுவான வருகை",
        "hi-IN": "सामान्य विज़िट",
    },
}

FIELD_LABELS: dict[str, dict[str, str]] = {
    "beneficiary_id": {"en-IN": "beneficiary ID", "ta-IN": "பயனாளி ஐடி", "hi-IN": "लाभार्थी आईडी"},
    "patient_name": {"en-IN": "patient name", "ta-IN": "நோயாளி பெயர்", "hi-IN": "मरीज़ का नाम"},
    "weight_kg": {"en-IN": "weight", "ta-IN": "எடை", "hi-IN": "वज़न"},
    "next_visit_date": {"en-IN": "next visit date", "ta-IN": "அடுத்த வருகை தேதி", "hi-IN": "अगली विज़िट की तारीख"},
    "visit_type": {"en-IN": "visit type", "ta-IN": "வருகை வகை", "hi-IN": "विज़िट का प्रकार"},
    "anc_completed": {"en-IN": "ANC checkup status", "ta-IN": "ANC பரிசோதனை நிலை", "hi-IN": "ANC जाँच की स्थिति"},
    "ifa_provided": {"en-IN": "IFA tablets", "ta-IN": "IFA மாத்திரை", "hi-IN": "IFA टैबलेट"},
    "vaccination_status": {"en-IN": "vaccination status", "ta-IN": "தடுப்பூசி நிலை", "hi-IN": "टीकाकरण की स्थिति"},
}

YES_NO: dict[str, dict[str, str]] = {
    "anc_true": {"en-IN": "completed", "ta-IN": "முடிந்தது", "hi-IN": "पूरी हुई"},
    "anc_false": {"en-IN": "not completed", "ta-IN": "முடிக்கவில்லை", "hi-IN": "नहीं हुई"},
    "anc_unknown": {"en-IN": "not recorded", "ta-IN": "பதிவாகவில்லை", "hi-IN": "दर्ज नहीं"},
    "ifa_true": {"en-IN": "provided", "ta-IN": "வழங்கப்பட்டது", "hi-IN": "दी गई"},
    "ifa_false": {"en-IN": "not provided", "ta-IN": "வழங்கப்படவில்லை", "hi-IN": "नहीं दी गई"},
    "ifa_unknown": {"en-IN": "not recorded", "ta-IN": "பதிவாகவில்லை", "hi-IN": "दर्ज नहीं"},
}

DANGER_WARNING: dict[str, dict[str, str]] = {
    "pregnancy": {
        "en-IN": (
            "Warning. Pregnancy danger sign detected. Please refer the patient to the "
            "nearest Primary Health Centre immediately."
        ),
        "ta-IN": (
            "எச்சரிக்கை. கர்ப்பகால ஆபத்து அறிகுறி கண்டறியப்பட்டது. நோயாளியை உடனடியாக "
            "அருகிலுள்ள ஆரம்ப சுகாதார நிலையத்திற்கு அழைத்துச் செல்லுங்கள்."
        ),
        "hi-IN": (
            "चेतावनी. गर्भावस्था का खतरे का संकेत मिला है. मरीज़ को तुरंत नज़दीकी "
            "प्राथमिक स्वास्थ्य केंद्र ले जाएँ."
        ),
    },
    "newborn": {
        "en-IN": (
            "Warning. Newborn danger sign detected. Please refer the baby to the "
            "nearest Primary Health Centre immediately."
        ),
        "ta-IN": (
            "எச்சரிக்கை. பிறந்த குழந்தைக்கு ஆபத்து அறிகுறி கண்டறியப்பட்டது. குழந்தையை "
            "உடனடியாக அருகிலுள்ள ஆரம்ப சுகாதார நிலையத்திற்கு அழைத்துச் செல்லுங்கள்."
        ),
        "hi-IN": (
            "चेतावनी. नवजात शिशु में खतरे का संकेत मिला है. शिशु को तुरंत नज़दीकी "
            "प्राथमिक स्वास्थ्य केंद्र ले जाएँ."
        ),
    },
    "postpartum": {
        "en-IN": (
            "Warning. Post-delivery danger sign detected. Please refer the mother to the "
            "nearest Primary Health Centre immediately."
        ),
        "ta-IN": (
            "எச்சரிக்கை. பிரசவத்திற்குப் பின் ஆபத்து அறிகுறி கண்டறியப்பட்டது. தாயை "
            "உடனடியாக அருகிலுள்ள ஆரம்ப சுகாதார நிலையத்திற்கு அழைத்துச் செல்லுங்கள்."
        ),
        "hi-IN": (
            "चेतावनी. प्रसव के बाद खतरे का संकेत मिला है. माँ को तुरंत नज़दीकी "
            "प्राथमिक स्वास्थ्य केंद्र ले जाएँ."
        ),
    },
}

TEMPLATES: dict[str, dict[str, str]] = {
    "confirm_suffix": {
        "en-IN": "Is this correct?",
        "ta-IN": "இது சரியா?",
        "hi-IN": "क्या यह सही है?",
    },
    "missing_prefix": {
        "en-IN": "I still need the {fields}. Please tell me.",
        "ta-IN": "{fields} தேவை. சொல்லுங்கள்.",
        "hi-IN": "मुझे अभी {fields} चाहिए. कृपया बताइए.",
    },
    "saved": {
        "en-IN": "Your visit record has been saved successfully. Follow-up tasks have been created.",
        "ta-IN": "உங்கள் வருகைப் பதிவு வெற்றிகரமாக சேமிக்கப்பட்டது. தொடர் பணிகள் உருவாக்கப்பட்டன.",
        "hi-IN": "आपका विज़िट रिकॉर्ड सफलतापूर्वक सहेजा गया. फ़ॉलो-अप कार्य बनाए गए.",
    },
    "corrected": {
        "en-IN": "Okay, I have corrected the {field} to {value}. Shall I save the record?",
        "ta-IN": "சரி, {field} {value} ஆக மாற்றிவிட்டேன். பதிவை சேமிக்கலாமா?",
        "hi-IN": "ठीक है, {field} को {value} कर दिया है. रिकॉर्ड सहेजूँ?",
    },
    "ask_correction": {
        "en-IN": "What should I change?",
        "ta-IN": "எதை மாற்ற வேண்டும்?",
        "hi-IN": "क्या बदलना है?",
    },
    "not_understood": {
        "en-IN": "Sorry, I did not catch that. Please say it again.",
        "ta-IN": "மன்னிக்கவும், புரியவில்லை. மீண்டும் சொல்லுங்கள்.",
        "hi-IN": "क्षमा करें, समझ नहीं आया. फिर से कहिए.",
    },
    "repeat_weight": {
        "en-IN": "The weight does not look right. Please repeat the weight.",
        "ta-IN": "எடை சரியாகத் தெரியவில்லை. எடையை மீண்டும் சொல்லுங்கள்.",
        "hi-IN": "वज़न ठीक नहीं लग रहा. कृपया वज़न दोबारा बताइए.",
    },
    "no_danger": {
        "en-IN": "No danger sign was found.",
        "ta-IN": "ஆபத்து அறிகுறி எதுவும் இல்லை.",
        "hi-IN": "कोई खतरे का संकेत नहीं मिला.",
    },
    "stt_start_failed": {
        "en-IN": "Speech recognition could not start. Please retry, or enter the visit manually.",
        "ta-IN": "பேச்சு அறிதல் தொடங்கவில்லை. மீண்டும் முயற்சிக்கவும் அல்லது கைமுறையாக உள்ளிடவும்.",
        "hi-IN": "स्पीच पहचान शुरू नहीं हुई. फिर कोशिश करें या मैन्युअल दर्ज करें.",
    },
    "stt_error": {
        "en-IN": "Speech recognition stopped. Please retry, or enter the visit manually.",
        "ta-IN": "பேச்சு அறிதல் நின்றுவிட்டது. மீண்டும் முயற்சிக்கவும் அல்லது கைமுறையாக உள்ளிடவும்.",
        "hi-IN": "स्पीच पहचान रुक गई. फिर कोशिश करें या मैन्युअल दर्ज करें.",
    },
    "session_error": {
        "en-IN": "The voice session ended unexpectedly. Please retry.",
        "ta-IN": "குரல் அமர்வு எதிர்பாராத விதமாக முடிந்தது. மீண்டும் முயற்சிக்கவும்.",
        "hi-IN": "वॉइस सत्र अचानक समाप्त हो गया. फिर कोशिश करें.",
    },
}


def t(key: str, language: str, **kwargs: str) -> str:
    """Look up a template and format it."""
    language = normalise_language(language)
    block = TEMPLATES.get(key)
    if not block:
        return key
    text = block.get(language) or block[DEFAULT_LANGUAGE]
    return text.format(**kwargs) if kwargs else text


def field_label(field: str, language: str) -> str:
    language = normalise_language(language)
    block = FIELD_LABELS.get(field)
    if not block:
        return field.replace("_", " ")
    return block.get(language) or block[DEFAULT_LANGUAGE]


def visit_type_label(visit_type: str, language: str) -> str:
    language = normalise_language(language)
    block = VISIT_TYPE_LABELS.get(visit_type) or VISIT_TYPE_LABELS["general"]
    return block.get(language) or block[DEFAULT_LANGUAGE]
