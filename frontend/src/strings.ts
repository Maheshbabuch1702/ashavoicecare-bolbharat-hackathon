import type { DangerHit, FollowUp, Language, VisitSummary } from "./types";

type Dict = Record<Language, string>;

export const S: Record<string, Dict> = {
  greetingMorning: {
    "en-IN": "Good morning, {name}",
    "ta-IN": "காலை வணக்கம், {name}",
    "hi-IN": "सुप्रभात, {name}",
  },
  greetingAfternoon: {
    "en-IN": "Good afternoon, {name}",
    "ta-IN": "மதிய வணக்கம், {name}",
    "hi-IN": "नमस्कार, {name}",
  },
  greetingEvening: {
    "en-IN": "Good evening, {name}",
    "ta-IN": "மாலை வணக்கம், {name}",
    "hi-IN": "शुभ संध्या, {name}",
  },
  greeting: {
    "en-IN": "Good morning, ASHA Worker",
    "ta-IN": "காலை வணக்கம், ஆஷா பணியாளரே",
    "hi-IN": "सुप्रभात, आशा कार्यकर्ता",
  },
  subtitle: {
    "en-IN": "Record your home visit using your voice.",
    "ta-IN": "உங்கள் வீட்டு வருகையை குரல் மூலம் பதிவு செய்யுங்கள்.",
    "hi-IN": "अपनी गृह भेंट आवाज़ से दर्ज करें।",
  },
  tapToSpeak: {
    "en-IN": "Tap to speak",
    "ta-IN": "பேச தட்டுங்கள்",
    "hi-IN": "बोलने के लिए टैप करें",
  },
  tapToStop: {
    "en-IN": "Tap to stop",
    "ta-IN": "நிறுத்த தட்டுங்கள்",
    "hi-IN": "रोकने के लिए टैप करें",
  },
  listening: {
    "en-IN": "Listening…",
    "ta-IN": "கேட்டுக்கொண்டிருக்கிறேன்…",
    "hi-IN": "सुन रही हूँ…",
  },
  processing: {
    "en-IN": "Building the record…",
    "ta-IN": "பதிவு தயாராகிறது…",
    "hi-IN": "रिकॉर्ड बन रहा है…",
  },
  todayVisits: {
    "en-IN": "Today's visits",
    "ta-IN": "இன்றைய வருகைகள்",
    "hi-IN": "आज की विज़िट",
  },
  followupsPending: {
    "en-IN": "Follow-ups pending",
    "ta-IN": "நிலுவையில் உள்ள பணிகள்",
    "hi-IN": "बाकी फ़ॉलो-अप",
  },
  totalVisits: {
    "en-IN": "All visits",
    "ta-IN": "மொத்த வருகைகள்",
    "hi-IN": "कुल विज़िट",
  },
  urgentAlerts: {
    "en-IN": "Urgent referrals",
    "ta-IN": "அவசர பரிந்துரைகள்",
    "hi-IN": "अत्यावश्यक रेफ़रल",
  },
  recentVisits: {
    "en-IN": "Recent visits",
    "ta-IN": "சமீபத்திய வருகைகள்",
    "hi-IN": "हाल की विज़िट",
  },
  noVisits: {
    "en-IN": "No visits recorded yet. Start with your voice or enter a record manually.",
    "ta-IN": "இன்னும் வருகை பதிவுகள் இல்லை. குரல் அல்லது கைமுறை பதிவுடன் தொடங்குங்கள்.",
    "hi-IN": "अभी कोई विज़िट दर्ज नहीं. आवाज़ या मैन्युअल प्रविष्टि से शुरू करें.",
  },
  recordTitle: {
    "en-IN": "Visit record",
    "ta-IN": "வருகைப் பதிவு",
    "hi-IN": "विज़िट रिकॉर्ड",
  },
  needsAnswer: {
    "en-IN": "Needs your answer",
    "ta-IN": "உங்கள் பதில் தேவை",
    "hi-IN": "आपका जवाब चाहिए",
  },
  confirm: {
    "en-IN": "Confirm & save",
    "ta-IN": "உறுதி செய்து சேமி",
    "hi-IN": "पुष्टि करें और सहेजें",
  },
  cancel: {
    "en-IN": "Cancel",
    "ta-IN": "ரத்து செய்",
    "hi-IN": "रद्द करें",
  },
  playAgain: {
    "en-IN": "Read it again",
    "ta-IN": "மீண்டும் கேட்க",
    "hi-IN": "फिर सुनें",
  },
  savedTitle: {
    "en-IN": "Record saved",
    "ta-IN": "பதிவு சேமிக்கப்பட்டது",
    "hi-IN": "रिकॉर्ड सहेजा गया",
  },
  savedSubtitle: {
    "en-IN": "Follow-up tasks were created automatically.",
    "ta-IN": "தொடர் பணிகள் தானாக உருவாக்கப்பட்டன.",
    "hi-IN": "फ़ॉलो-अप कार्य अपने आप बन गए.",
  },
  newVisit: {
    "en-IN": "New visit",
    "ta-IN": "புதிய வருகை",
    "hi-IN": "नई विज़िट",
  },
  appTagline: {
    "en-IN": "Voice-first health records",
    "ta-IN": "குரல் வழி சுகாதாரப் பதிவுகள்",
    "hi-IN": "आवाज़-आधारित स्वास्थ्य रिकॉर्ड",
  },
  newVisitTitle: {
    "en-IN": "Start a new visit",
    "ta-IN": "புதிய வருகையைத் தொடங்குங்கள்",
    "hi-IN": "नई विज़िट शुरू करें",
  },
  newVisitBody: {
    "en-IN": "Use the microphone for a hands-free record, or type the same fields if the mic is unavailable.",
    "ta-IN": "கைகள் இல்லாமல் பதிவு செய்ய மைக்ரோஃபோனைப் பயன்படுத்துங்கள், அல்லது மைக்ரோஃபோன் இல்லையெனில் அதே விவரங்களை தட்டச்சு செய்யுங்கள்.",
    "hi-IN": "बिना हाथ लगाए रिकॉर्ड के लिए माइक्रोफ़ोन इस्तेमाल करें, या माइक न होने पर वही जानकारी टाइप करें.",
  },
  startVoice: {
    "en-IN": "Start voice visit",
    "ta-IN": "குரல் வருகையைத் தொடங்கு",
    "hi-IN": "वॉइस विज़िट शुरू करें",
  },
  enterManually: {
    "en-IN": "Enter manually",
    "ta-IN": "கைமுறையாக உள்ளிடு",
    "hi-IN": "मैन्युअल रूप से दर्ज करें",
  },
  manualFallback: {
    "en-IN": "Can't use the mic? Enter the visit manually.",
    "ta-IN": "மைக்ரோஃபோன் பயன்படுத்த முடியவில்லையா? வருகையை கைமுறையாக உள்ளிடுங்கள்.",
    "hi-IN": "माइक नहीं चल रहा? विज़िट मैन्युअल रूप से दर्ज करें.",
  },
  dangerAlert: {
    "en-IN": "Danger sign detected",
    "ta-IN": "ஆபத்து அறிகுறி",
    "hi-IN": "खतरे का संकेत",
  },
  referNow: {
    "en-IN": "Refer to the PHC now",
    "ta-IN": "உடனே PHC-க்கு அழைத்துச் செல்லுங்கள்",
    "hi-IN": "तुरंत PHC ले जाएँ",
  },
  offline: {
    "en-IN": "No internet connection",
    "ta-IN": "இணைய இணைப்பு இல்லை",
    "hi-IN": "इंटरनेट कनेक्शन नहीं",
  },
  offlineNote: {
    "en-IN": "Records cannot be saved until the connection returns.",
    "ta-IN": "இணைப்பு திரும்பும் வரை பதிவுகளை சேமிக்க முடியாது.",
    "hi-IN": "कनेक्शन लौटने तक रिकॉर्ड सहेजे नहीं जा सकते.",
  },
  micDenied: {
    "en-IN": "Microphone permission is needed.",
    "ta-IN": "மைக்ரோஃபோன் அனுமதி தேவை.",
    "hi-IN": "माइक्रोफ़ोन की अनुमति चाहिए.",
  },
  speakNow: {
    "en-IN": "Speak now",
    "ta-IN": "இப்போது பேசுங்கள்",
    "hi-IN": "अब बोलिए",
  },
  correctionHint: {
    "en-IN": "Say “No, weight is 55.5 kilo” to correct any field.",
    "ta-IN": "“இல்லை, எடை 55.5 கிலோ” எனச் சொல்லி திருத்தலாம்.",
    "hi-IN": "सुधार के लिए “नहीं, वज़न 55.5 किलो” कहें.",
  },
  transcript: {
    "en-IN": "Speech transcript",
    "ta-IN": "பேச்சு உரை",
    "hi-IN": "बोली गई बात",
  },
  followups: {
    "en-IN": "Follow-up tasks",
    "ta-IN": "தொடர் பணிகள்",
    "hi-IN": "फ़ॉलो-अप कार्य",
  },
  markDone: {
    "en-IN": "Mark done",
    "ta-IN": "முடிந்தது",
    "hi-IN": "पूरा हुआ",
  },
  notSpecified: {
    "en-IN": "Not recorded",
    "ta-IN": "பதிவாகவில்லை",
    "hi-IN": "दर्ज नहीं",
  },
  priorityUrgent: { "en-IN": "Urgent", "ta-IN": "அவசரம்", "hi-IN": "अत्यावश्यक" },
  priorityHigh: { "en-IN": "High", "ta-IN": "அதிகம்", "hi-IN": "उच्च" },
  priorityNormal: { "en-IN": "Normal", "ta-IN": "சாதாரணம்", "hi-IN": "सामान्य" },
  connectFirst: {
    "en-IN": "Connecting to the voice service…",
    "ta-IN": "குரல் சேவையுடன் இணைக்கிறது…",
    "hi-IN": "वॉइस सेवा से जुड़ रहे हैं…",
  },
  errorGeneric: {
    "en-IN": "Something went wrong.",
    "ta-IN": "ஏதோ தவறு நடந்தது.",
    "hi-IN": "कुछ गलत हो गया.",
  },
  errorInsecure: {
    "en-IN": "Microphone access needs a secure page. Open the app at https:// or http://127.0.0.1:8000 in Chrome or Edge, then allow the microphone.",
    "ta-IN": "மைக்ரோஃபோன் அணுகலுக்கு பாதுகாப்பான பக்கம் தேவை. Chrome அல்லது Edge-ல் https:// அல்லது http://127.0.0.1:8000 திறந்து மைக்ரோஃபோனை அனுமதிக்கவும்.",
    "hi-IN": "माइक्रोफ़ोन के लिए सुरक्षित पेज चाहिए. Chrome या Edge में https:// या http://127.0.0.1:8000 खोलकर माइक्रोफ़ोन allow करें.",
  },
  errorIframe: {
    "en-IN": "This preview panel is blocking microphone access. Open the app in its own browser tab.",
    "ta-IN": "இந்த முன்னோட்ட சாளரம் மைக்ரோஃபோன் அணுகலைத் தடுக்கிறது. பயன்பாட்டை தனி உலாவி தாவலில் திறக்கவும்.",
    "hi-IN": "यह प्रीव्यू पैनल माइक्रोफ़ोन रोक रहा है. ऐप को अपने ब्राउज़र टैब में खोलें.",
  },
  errorMicDenied: {
    "en-IN": "The microphone is blocked. Allow it in the address bar (site settings), then try again.",
    "ta-IN": "மைக்ரோஃபோன் தடுக்கப்பட்டுள்ளது. முகவரி பட்டியில் அனுமதித்து மீண்டும் முயற்சிக்கவும்.",
    "hi-IN": "माइक्रोफ़ोन blocked है. एड्रेस बार में allow करके फिर कोशिश करें.",
  },
  errorNoMic: {
    "en-IN": "No microphone was found. Connect one, or enter the visit manually.",
    "ta-IN": "மைக்ரோஃபோன் கிடைக்கவில்லை. இணைக்கவும் அல்லது கைமுறையாக உள்ளிடவும்.",
    "hi-IN": "कोई माइक्रोफ़ोन नहीं मिला. जोड़ें या मैन्युअल रूप से दर्ज करें.",
  },
  errorMicBusy: {
    "en-IN": "The microphone is busy in another app. Close it, then try again.",
    "ta-IN": "மைக்ரோஃபோன் வேறு செயலியில் பயன்பாட்டில் உள்ளது. அதை மூடி மீண்டும் முயற்சிக்கவும்.",
    "hi-IN": "माइक्रोफ़ोन किसी दूसरे ऐप में चल रहा है. उसे बंद करके फिर कोशिश करें.",
  },
  errorUnsupported: {
    "en-IN": "This browser cannot capture audio. Use Chrome or Edge, or enter the visit manually.",
    "ta-IN": "இந்த உலாவி ஒலியைப் பதிவு செய்ய முடியாது. Chrome அல்லது Edge பயன்படுத்தவும் அல்லது கைமுறையாக உள்ளிடவும்.",
    "hi-IN": "यह ब्राउज़र ऑडियो नहीं ले सकता. Chrome या Edge use करें, या मैन्युअल दर्ज करें.",
  },
  errorSocket: {
    "en-IN": "The voice service did not answer. Check the backend, then retry — or enter the visit manually.",
    "ta-IN": "குரல் சேவை பதிலளிக்கவில்லை. பின்தளத்தைச் சரிபார்த்து மீண்டும் முயற்சிக்கவும் — அல்லது கைமுறையாக உள்ளிடவும்.",
    "hi-IN": "वॉइस सेवा ने जवाब नहीं दिया. बैकएंड जाँचें और फिर कोशिश करें — या मैन्युअल दर्ज करें.",
  },
  errorVoiceService: {
    "en-IN": "Speech recognition could not start. You can retry or enter the visit manually.",
    "ta-IN": "பேச்சு அறிதல் தொடங்கவில்லை. மீண்டும் முயற்சிக்கவும் அல்லது கைமுறையாக உள்ளிடவும்.",
    "hi-IN": "स्पीच पहचान शुरू नहीं हुई. फिर कोशिश करें या मैन्युअल दर्ज करें.",
  },
  errorSaveManual: {
    "en-IN": "The visit could not be saved. Check the backend connection, then try again.",
    "ta-IN": "வருகையைச் சேமிக்க முடியவில்லை. பின்தள இணைப்பைச் சரிபார்த்து மீண்டும் முயற்சிக்கவும்.",
    "hi-IN": "विज़िट सहेजी नहीं जा सकी. बैकएंड कनेक्शन जाँचें और फिर कोशिश करें.",
  },
  errorLoadVisit: {
    "en-IN": "This visit could not be opened. Check the backend connection, then try again.",
    "ta-IN": "இந்த வருகையைத் திறக்க முடியவில்லை. பின்தள இணைப்பைச் சரிபார்த்து மீண்டும் முயற்சிக்கவும்.",
    "hi-IN": "यह विज़िट खोली नहीं जा सकी. बैकएंड कनेक्शन जाँचें और फिर कोशिश करें.",
  },
  errorUpdateVisit: {
    "en-IN": "The changes could not be saved. Check the backend connection, then try again.",
    "ta-IN": "மாற்றங்களைச் சேமிக்க முடியவில்லை. பின்தள இணைப்பைச் சரிபார்த்து மீண்டும் முயற்சிக்கவும்.",
    "hi-IN": "बदलाव सहेजे नहीं जा सके. बैकएंड कनेक्शन जाँचें और फिर कोशिश करें.",
  },
  retry: { "en-IN": "Retry", "ta-IN": "மீண்டும்", "hi-IN": "फिर कोशिश करें" },
  openInNewTab: { "en-IN": "Open in a new tab", "ta-IN": "புதிய தாவலில் திற", "hi-IN": "नए टैब में खोलें" },
  useManual: { "en-IN": "Enter manually", "ta-IN": "கைமுறை உள்ளீடு", "hi-IN": "मैन्युअल दर्ज करें" },
  dismiss: { "en-IN": "Dismiss", "ta-IN": "மூடு", "hi-IN": "बंद करें" },
  draftBadge: { "en-IN": "Draft", "ta-IN": "வரைவு", "hi-IN": "ड्राफ़्ट" },
  confidenceLow: {
    "en-IN": "Please confirm",
    "ta-IN": "உறுதி செய்யுங்கள்",
    "hi-IN": "पुष्टि करें",
  },
  understandNote: {
    "en-IN": "Danger signs are checked against a fixed government guideline list. The app does not diagnose or prescribe.",
    "ta-IN": "ஆபத்து அறிகுறிகள் அரசு வழிகாட்டி பட்டியலின்படி மட்டுமே சரிபார்க்கப்படும். இது நோயறிதல் அல்ல.",
    "hi-IN": "खतरे के संकेत सिर्फ़ सरकारी दिशानिर्देश सूची से जाँचे जाते हैं. ऐप निदान या दवा नहीं बताता.",
  },
  viewAll: { "en-IN": "View all", "ta-IN": "அனைத்தையும் பார்", "hi-IN": "सभी देखें" },
  homeNav: { "en-IN": "Home", "ta-IN": "முகப்பு", "hi-IN": "होम" },
  followupsNav: { "en-IN": "Follow-ups", "ta-IN": "தொடர் பணிகள்", "hi-IN": "फ़ॉलो-अप" },
  historyNav: { "en-IN": "History", "ta-IN": "வரலாறு", "hi-IN": "इतिहास" },
  totalVisitsNav: { "en-IN": "Visits", "ta-IN": "வருகைகள்", "hi-IN": "विज़िट" },
  pending: { "en-IN": "pending", "ta-IN": "நிலுவை", "hi-IN": "बाकी" },
  urgent: { "en-IN": "urgent", "ta-IN": "அவசரம்", "hi-IN": "अत्यावश्यक" },
  urgentReferralsPending: {
    "en-IN": "{count} urgent referral pending",
    "ta-IN": "{count} அவசர பரிந்துரை நிலுவையில்",
    "hi-IN": "{count} अत्यावश्यक रेफ़रल बाकी",
  },
  urgentReferralsPendingPlural: {
    "en-IN": "{count} urgent referrals pending",
    "ta-IN": "{count} அவசர பரிந்துரைகள் நிலுவையில்",
    "hi-IN": "{count} अत्यावश्यक रेफ़रल बाकी",
  },
  tapOpenFollowups: {
    "en-IN": "Tap to open the follow-up list",
    "ta-IN": "தொடர் பணிகள் பட்டியலைத் திறக்க தட்டுங்கள்",
    "hi-IN": "फ़ॉलो-अप सूची खोलने के लिए टैप करें",
  },
  manualTitle: {
    "en-IN": "Enter a visit manually",
    "ta-IN": "வருகையை கைமுறையாக உள்ளிடுங்கள்",
    "hi-IN": "विज़िट मैन्युअल रूप से दर्ज करें",
  },
  manualSubtitle: {
    "en-IN": "Type only what the worker actually observed. Blank fields stay blank — they are never filled automatically.",
    "ta-IN": "பணியாளர் உண்மையில் கண்டதை மட்டும் உள்ளிடுங்கள். காலி புலங்கள் காலியாகவே இருக்கும் — தானாக நிரப்பப்படாது.",
    "hi-IN": "सिर्फ़ वही लिखें जो कार्यकर्ता ने देखा. खाली फ़ील्ड खाली रहेंगे — अपने आप नहीं भरेंगे.",
  },
  manualIdentityRequired: {
    "en-IN": "Enter a patient name or beneficiary ID before saving.",
    "ta-IN": "சேமிக்கும் முன் நோயாளி பெயர் அல்லது பயனாளி ஐடி உள்ளிடுங்கள்.",
    "hi-IN": "सहेजने से पहले मरीज़ का नाम या लाभार्थी आईडी दर्ज करें.",
  },
  manualSave: { "en-IN": "Save visit record", "ta-IN": "வருகைப் பதிவைச் சேமி", "hi-IN": "विज़िट रिकॉर्ड सहेजें" },
  manualSaving: { "en-IN": "Saving…", "ta-IN": "சேமிக்கிறது…", "hi-IN": "सहेज रहे हैं…" },
  manualName: { "en-IN": "Patient / newborn name", "ta-IN": "நோயாளி / குழந்தையின் பெயர்", "hi-IN": "मरीज़ / शिशु का नाम" },
  manualNameHint: {
    "en-IN": "For a newborn, write “Baby of …” if the baby has no name yet.",
    "ta-IN": "குழந்தைக்கு பெயர் இல்லையெனில் “...வின் குழந்தை” என எழுதுங்கள்.",
    "hi-IN": "शिशु का नाम न हो तो “... का बच्चा” लिखें.",
  },
  manualId: { "en-IN": "Beneficiary ID", "ta-IN": "பயனாளி ஐடி", "hi-IN": "लाभार्थी आईडी" },
  manualVisitType: { "en-IN": "Visit type", "ta-IN": "வருகை வகை", "hi-IN": "विज़िट का प्रकार" },
  manualWeight: { "en-IN": "Weight (kg)", "ta-IN": "எடை (கிலோ)", "hi-IN": "वज़न (किलो)" },
  manualBp: { "en-IN": "Blood pressure", "ta-IN": "இரத்த அழுத்தம்", "hi-IN": "रक्तचाप" },
  manualBpPlaceholder: { "en-IN": "e.g. 120/80", "ta-IN": "எ.கா. 120/80", "hi-IN": "जैसे 120/80" },
  manualAnc: { "en-IN": "ANC checkup", "ta-IN": "ANC பரிசோதனை", "hi-IN": "ANC जाँच" },
  manualIfa: { "en-IN": "IFA tablets", "ta-IN": "IFA மாத்திரை", "hi-IN": "IFA टैबलेट" },
  manualVaccination: { "en-IN": "Vaccination status", "ta-IN": "தடுப்பூசி நிலை", "hi-IN": "टीकाकरण स्थिति" },
  manualVaccinesDue: { "en-IN": "Vaccines due", "ta-IN": "நிலுவை தடுப்பூசிகள்", "hi-IN": "बाकी टीके" },
  manualNextVisit: { "en-IN": "Next visit date", "ta-IN": "அடுத்த வருகை தேதி", "hi-IN": "अगली विज़िट की तारीख" },
  nextVisitShort: { "en-IN": "Next visit", "ta-IN": "அடுத்த வருகை", "hi-IN": "अगली विज़िट" },
  manualObservations: { "en-IN": "Observations", "ta-IN": "குறிப்புகள்", "hi-IN": "टिप्पणियाँ" },
  manualObservationsHint: {
    "en-IN": "Record what was seen or said. Danger signs in this note are checked by the same fixed rule engine.",
    "ta-IN": "கண்டதையும் சொன்னதையும் பதிவு செய்யுங்கள். இதில் உள்ள ஆபத்து அறிகுறிகள் அதே விதிகள் மூலம் சரிபார்க்கப்படும்.",
    "hi-IN": "जो देखा या कहा गया वह लिखें. इस नोट के खतरे के संकेत उसी नियम प्रणाली से जाँचे जाएँगे.",
  },
  notRecordedOption: { "en-IN": "Not recorded", "ta-IN": "பதிவாகவில்லை", "hi-IN": "दर्ज नहीं" },
  completedOption: { "en-IN": "Completed", "ta-IN": "முடிந்தது", "hi-IN": "पूरी हुई" },
  notCompletedOption: { "en-IN": "Not completed", "ta-IN": "முடிக்கவில்லை", "hi-IN": "नहीं हुई" },
  providedOption: { "en-IN": "Provided", "ta-IN": "வழங்கப்பட்டது", "hi-IN": "दी गई" },
  notProvidedOption: { "en-IN": "Not provided", "ta-IN": "வழங்கப்படவில்லை", "hi-IN": "नहीं दी गई" },
  givenOption: { "en-IN": "Given", "ta-IN": "வழங்கப்பட்டது", "hi-IN": "हो गया" },
  dueOption: { "en-IN": "Due", "ta-IN": "நிலுவை", "hi-IN": "बाकी" },
  manualSavedToast: {
    "en-IN": "Visit saved and follow-ups created.",
    "ta-IN": "வருகை சேமிக்கப்பட்டது; தொடர் பணிகள் உருவாக்கப்பட்டன.",
    "hi-IN": "विज़िट सहेजी गई और फ़ॉलो-अप बने.",
  },
  searchPlaceholder: {
    "en-IN": "Search by name, ID, or note…",
    "ta-IN": "பெயர், ஐடி அல்லது குறிப்பால் தேடுங்கள்…",
    "hi-IN": "नाम, आईडी या नोट से खोजें…",
  },
  filterType: { "en-IN": "Visit type", "ta-IN": "வருகை வகை", "hi-IN": "विज़िट प्रकार" },
  allTypes: { "en-IN": "All visit types", "ta-IN": "அனைத்து வகைகள்", "hi-IN": "सभी प्रकार" },
  allPatients: { "en-IN": "All patients", "ta-IN": "அனைத்து நோயாளிகள்", "hi-IN": "सभी मरीज़" },
  dateFrom: { "en-IN": "From", "ta-IN": "இருந்து", "hi-IN": "से" },
  dateTo: { "en-IN": "To", "ta-IN": "வரை", "hi-IN": "तक" },
  clearFilters: { "en-IN": "Clear filters", "ta-IN": "வடிகட்டிகளை அழி", "hi-IN": "फ़िल्टर हटाएँ" },
  resultsCount: {
    "en-IN": "{count} visits",
    "ta-IN": "{count} வருகைகள்",
    "hi-IN": "{count} विज़िट",
  },
  resultsCountOne: {
    "en-IN": "1 visit",
    "ta-IN": "1 வருகை",
    "hi-IN": "1 विज़िट",
  },
  noResults: {
    "en-IN": "No visits match these filters.",
    "ta-IN": "இந்த வடிகட்டிகளுக்கு வருகைகள் இல்லை.",
    "hi-IN": "इन फ़िल्टर से कोई विज़िट नहीं मिली.",
  },
  patientLookup: { "en-IN": "Patient lookup", "ta-IN": "நோயாளி தேடல்", "hi-IN": "मरीज़ खोज" },
  visitDetail: { "en-IN": "Visit details", "ta-IN": "வருகை விவரங்கள்", "hi-IN": "विज़िट विवरण" },
  back: { "en-IN": "Back", "ta-IN": "பின்செல்", "hi-IN": "वापस" },
  editRecord: { "en-IN": "Edit record", "ta-IN": "பதிவைத் திருத்து", "hi-IN": "रिकॉर्ड संपादित करें" },
  saveChanges: { "en-IN": "Save changes", "ta-IN": "மாற்றங்களைச் சேமி", "hi-IN": "बदलाव सहेजें" },
  savingChanges: { "en-IN": "Saving…", "ta-IN": "சேமிக்கிறது…", "hi-IN": "सहेज रहे हैं…" },
  recordedOn: { "en-IN": "Recorded", "ta-IN": "பதிவு செய்யப்பட்டது", "hi-IN": "दर्ज किया गया" },
  corrections: { "en-IN": "Corrections", "ta-IN": "திருத்தங்கள்", "hi-IN": "सुधार" },
  noCorrections: {
    "en-IN": "No manual corrections yet.",
    "ta-IN": "இன்னும் கைமுறை திருத்தங்கள் இல்லை.",
    "hi-IN": "अभी कोई मैन्युअल सुधार नहीं.",
  },
  editedNote: {
    "en-IN": "Edits correct the stored fields. Danger alerts and follow-ups stay as they were recorded at the visit, so an emergency flag is never silently removed.",
    "ta-IN": "திருத்தங்கள் சேமித்த புலங்களை மட்டும் மாற்றும். ஆபத்து எச்சரிக்கைகளும் தொடர் பணிகளும் வருகையின் போது பதிவானபடியே இருக்கும்; அவசர எச்சரிக்கை மறைக்கப்படாது.",
    "hi-IN": "संपादन सहेजे गए फ़ील्ड बदलते हैं. खतरे के अलर्ट और फ़ॉलो-अप विज़िट के समय जैसे थे वैसे ही रहते हैं; आपातकालीन चेतावनी चुपचाप नहीं हटती.",
  },
  toastUpdated: { "en-IN": "Visit record updated.", "ta-IN": "வருகைப் பதிவு புதுப்பிக்கப்பட்டது.", "hi-IN": "विज़िट रिकॉर्ड अपडेट हुआ." },
  confirmDoneTitle: { "en-IN": "Mark this task done?", "ta-IN": "இந்தப் பணியை முடிந்ததாகக் குறிக்கவா?", "hi-IN": "इस कार्य को पूरा मार्क करें?" },
  confirmDoneBody: {
    "en-IN": "You can undo this for a few seconds after confirming.",
    "ta-IN": "உறுதி செய்த பிறகு சில வினாடிகளுக்கு செயல்தவிர்க்கலாம்.",
    "hi-IN": "पुष्टि के बाद कुछ सेकंड तक इसे वापस ले सकते हैं.",
  },
  confirmDone: { "en-IN": "Yes, mark done", "ta-IN": "ஆம், முடிந்தது", "hi-IN": "हाँ, पूरा हुआ" },
  undo: { "en-IN": "Undo", "ta-IN": "செயல்தவிர்", "hi-IN": "वापस लें" },
  taskDone: { "en-IN": "Task marked done.", "ta-IN": "பணி முடிந்ததாகக் குறிக்கப்பட்டது.", "hi-IN": "कार्य पूरा मार्क हुआ." },
  taskRestored: { "en-IN": "Task restored.", "ta-IN": "பணி மீட்டெடுக்கப்பட்டது.", "hi-IN": "कार्य बहाल हुआ." },
  dueOverdue: { "en-IN": "Overdue", "ta-IN": "தாமதம்", "hi-IN": "देय पार" },
  dueToday: { "en-IN": "Due today", "ta-IN": "இன்று", "hi-IN": "आज देय" },
  dueSoon: { "en-IN": "Next 7 days", "ta-IN": "அடுத்த 7 நாட்கள்", "hi-IN": "अगले 7 दिन" },
  dueLater: { "en-IN": "Later", "ta-IN": "பின்னர்", "hi-IN": "बाद में" },
  filterAll: { "en-IN": "All", "ta-IN": "அனைத்தும்", "hi-IN": "सभी" },
  filterOverdue: { "en-IN": "Overdue", "ta-IN": "தாமதம்", "hi-IN": "देय पार" },
  filterUrgent: { "en-IN": "Urgent", "ta-IN": "அவசரம்", "hi-IN": "अत्यावश्यक" },
  filterUpcoming: { "en-IN": "Upcoming", "ta-IN": "வரவிருக்கும்", "hi-IN": "आगामी" },
  noPendingTasks: {
    "en-IN": "No pending tasks. Everything is up to date.",
    "ta-IN": "நிலுவை பணிகள் இல்லை. அனைத்தும் பூர்த்தி.",
    "hi-IN": "कोई बाकी कार्य नहीं. सब पूरा है.",
  },
  generatedAutomatically: {
    "en-IN": "Generated automatically from saved visit records, sorted by due date.",
    "ta-IN": "சேமித்த வருகைப் பதிவுகளிலிருந்து தானாக உருவாக்கப்பட்டு, தேதி வரிசையில் அடுக்கப்பட்டது.",
    "hi-IN": "सहेजे गए विज़िट रिकॉर्ड से अपने आप बने, देय तिथि के क्रम में.",
  },
  detailReferral: {
    "en-IN": "{who} · danger sign detected. Refer to the nearest PHC now.",
    "ta-IN": "{who} · ஆபத்து அறிகுறி. உடனே அருகிலுள்ள PHC-க்கு அழைத்துச் செல்லுங்கள்.",
    "hi-IN": "{who} · खतरे का संकेत. तुरंत नज़दीकी PHC ले जाएँ.",
  },
  detailNextVisit: {
    "en-IN": "{who} · scheduled follow-up visit",
    "ta-IN": "{who} · திட்டமிட்ட தொடர் வருகை",
    "hi-IN": "{who} · निर्धारित फ़ॉलो-अप विज़िट",
  },
  detailScheduleVisit: {
    "en-IN": "{who} · no next visit date was recorded",
    "ta-IN": "{who} · அடுத்த வருகை தேதி பதிவாகவில்லை",
    "hi-IN": "{who} · अगली विज़िट की तारीख दर्ज नहीं",
  },
  detailIFA: {
    "en-IN": "{who} · check IFA tablet use at the next contact",
    "ta-IN": "{who} · அடுத்த தொடர்பில் IFA மாத்திரை பயன்பாட்டைச் சரிபார்க்கவும்",
    "hi-IN": "{who} · अगले संपर्क में IFA टैबलेट उपयोग जाँचें",
  },
  detailVaccination: {
    "en-IN": "{who} · vaccination details were not recorded",
    "ta-IN": "{who} · தடுப்பூசி விவரங்கள் பதிவாகவில்லை",
    "hi-IN": "{who} · टीकाकरण विवरण दर्ज नहीं",
  },
  detailVaccinationDue: {
    "en-IN": "{who} · vaccines pending",
    "ta-IN": "{who} · தடுப்பூசிகள் நிலுவையில்",
    "hi-IN": "{who} · टीके बाकी",
  },
  detailANC: {
    "en-IN": "{who} · ANC checkup was not confirmed as completed",
    "ta-IN": "{who} · ANC பரிசோதனை முடிந்ததாக உறுதி செய்யப்படவில்லை",
    "hi-IN": "{who} · ANC जाँच पूरी होने की पुष्टि नहीं",
  },
  detailHBNC: {
    "en-IN": "{who} · next HBNC home visit and danger-sign screening",
    "ta-IN": "{who} · அடுத்த HBNC வீட்டு வருகை மற்றும் ஆபத்து அறிகுறி சோதனை",
    "hi-IN": "{who} · अगली HBNC गृह भेंट और खतरे के संकेत जाँच",
  },
  beneficiaryGeneric: { "en-IN": "Beneficiary", "ta-IN": "பயனாளி", "hi-IN": "लाभार्थी" },
  newbornGeneric: { "en-IN": "Newborn", "ta-IN": "புதிதாகப் பிறந்த குழந்தை", "hi-IN": "नवजात" },
  speakingInterrupt: {
    "en-IN": "Speaking… interrupt me to correct",
    "ta-IN": "பேசுகிறேன்… திருத்த பேசுங்கள்",
    "hi-IN": "बोल रही हूँ… सुधार के लिए बोलें",
  },
  willBeCreated: { "en-IN": "will be created", "ta-IN": "உருவாக்கப்படும்", "hi-IN": "बनाए जाएँगे" },
  live: { "en-IN": "live", "ta-IN": "நேரலை", "hi-IN": "लाइव" },
  typeInstead: { "en-IN": "Type the note into this visit", "ta-IN": "இந்த வருகையில் குறிப்பைத் தட்டச்சு செய்", "hi-IN": "इस विज़िट में नोट टाइप करें" },
  typePlaceholder: {
    "en-IN": "Lakshmi, ID ASHA102, weight 55 kilo…",
    "ta-IN": "லட்சுமி, ஐடி ASHA102, எடை 55 கிலோ…",
    "hi-IN": "लक्ष्मी, आईडी ASHA102, वज़न 55 किलो…",
  },
  send: { "en-IN": "Send", "ta-IN": "அனுப்பு", "hi-IN": "भेजें" },
  typeHint: {
    "en-IN": "Injects text into the same streaming pipeline. Use it if the venue microphone fails.",
    "ta-IN": "அதே ஸ்ட்ரீமிங் பாதையில் உரையைச் செலுத்தும். மைக்ரோஃபோன் வேலை செய்யவில்லை எனில் பயன்படுத்துங்கள்.",
    "hi-IN": "यही टेक्स्ट स्ट्रीमिंग पाइपलाइन में जाता है. माइक न चले तो इसका उपयोग करें.",
  },
  switchToManual: {
    "en-IN": "Switch to manual entry",
    "ta-IN": "கைமுறை உள்ளீட்டுக்கு மாறு",
    "hi-IN": "मैन्युअल प्रविष्टि पर जाएँ",
  },
  noSpeechYet: {
    "en-IN": "No speech yet? Check the mic permission, or switch to manual entry.",
    "ta-IN": "இன்னும் பேச்சு இல்லையா? மைக்ரோஃபோன் அனுமதியைச் சரிபார்க்கவும் அல்லது கைமுறைக்கு மாறவும்.",
    "hi-IN": "अभी आवाज़ नहीं? माइक अनुमति जाँचें या मैन्युअल पर जाएँ.",
  },
  guideline: { "en-IN": "Guideline", "ta-IN": "வழிகாட்டி", "hi-IN": "दिशानिर्देश" },
  extractionRules: { "en-IN": "Rules", "ta-IN": "விதிகள்", "hi-IN": "नियम" },
  extractionLlm: { "en-IN": "AI model", "ta-IN": "AI மாதிரி", "hi-IN": "AI मॉडल" },
  extractionManual: { "en-IN": "Manual", "ta-IN": "கைமுறை", "hi-IN": "मैन्युअल" },
  extractionLabel: { "en-IN": "Extraction", "ta-IN": "பிரித்தெடுத்தல்", "hi-IN": "निष्कर्षण" },
  languageLabel: { "en-IN": "Language", "ta-IN": "மொழி", "hi-IN": "भाषा" },
  statusConfirmed: { "en-IN": "Confirmed", "ta-IN": "உறுதி", "hi-IN": "पुष्ट" },
  dangerShort: { "en-IN": "DANGER", "ta-IN": "ஆபத்து", "hi-IN": "खतरा" },
  babyNotNamed: {
    "en-IN": "Newborn · name not recorded",
    "ta-IN": "புதிதாகப் பிறந்த குழந்தை · பெயர் பதிவாகவில்லை",
    "hi-IN": "नवजात · नाम दर्ज नहीं",
  },
  beneficiaryNotNamed: {
    "en-IN": "Beneficiary · name not recorded",
    "ta-IN": "பயனாளி · பெயர் பதிவாகவில்லை",
    "hi-IN": "लाभार्थी · नाम दर्ज नहीं",
  },
  unknownValue: { "en-IN": "—", "ta-IN": "—", "hi-IN": "—" },
  workerProfile: { "en-IN": "Worker profile", "ta-IN": "பணியாளர் சுயவிவரம்", "hi-IN": "कार्यकर्ता प्रोफ़ाइल" },
  workerName: { "en-IN": "Name", "ta-IN": "பெயர்", "hi-IN": "नाम" },
  workerVillage: { "en-IN": "Village / area", "ta-IN": "கிராமம் / பகுதி", "hi-IN": "गाँव / क्षेत्र" },
  saveProfile: { "en-IN": "Save profile", "ta-IN": "சுயவிவரத்தைச் சேமி", "hi-IN": "प्रोफ़ाइल सहेजें" },
  profileSaved: { "en-IN": "Profile updated.", "ta-IN": "சுயவிவரம் புதுப்பிக்கப்பட்டது.", "hi-IN": "प्रोफ़ाइल अपडेट हुई." },
  profileHint: {
    "en-IN": "Synthetic demo profile only. Stored on this device.",
    "ta-IN": "செயற்கை டெமோ சுயவிவரம் மட்டும். இந்த சாதனத்தில் சேமிக்கப்படும்.",
    "hi-IN": "सिर्फ़ सिंथेटिक डेमो प्रोफ़ाइल. इस डिवाइस पर सहेजी जाती है.",
  },
  quickActions: { "en-IN": "Quick actions", "ta-IN": "விரைவு செயல்கள்", "hi-IN": "त्वरित कार्य" },
  voiceNeedsMic: {
    "en-IN": "Voice needs microphone permission.",
    "ta-IN": "குரலுக்கு மைக்ரோஃபோன் அனுமதி தேவை.",
    "hi-IN": "वॉइस के लिए माइक अनुमति चाहिए.",
  },
  startingMic: { "en-IN": "Starting microphone…", "ta-IN": "மைக்ரோஃபோன் தொடங்குகிறது…", "hi-IN": "माइक्रोफ़ोन शुरू हो रहा है…" },
  visitSaved: { "en-IN": "Visit saved.", "ta-IN": "வருகை சேமிக்கப்பட்டது.", "hi-IN": "विज़िट सहेजी गई." },
};

export const FIELD_LABELS: Record<string, Dict> = {
  beneficiary_id: { "en-IN": "Beneficiary ID", "ta-IN": "பயனாளி ஐடி", "hi-IN": "लाभार्थी आईडी" },
  patient_name: { "en-IN": "Patient name", "ta-IN": "நோயாளி பெயர்", "hi-IN": "मरीज़ का नाम" },
  visit_type: { "en-IN": "Visit type", "ta-IN": "வருகை வகை", "hi-IN": "विज़िट का प्रकार" },
  weight_kg: { "en-IN": "Weight", "ta-IN": "எடை", "hi-IN": "वज़न" },
  bp: { "en-IN": "Blood pressure", "ta-IN": "இரத்த அழுத்தம்", "hi-IN": "रक्तचाप" },
  anc_completed: { "en-IN": "ANC checkup", "ta-IN": "ANC பரிசோதனை", "hi-IN": "ANC जाँच" },
  ifa_provided: { "en-IN": "IFA tablets", "ta-IN": "IFA மாத்திரை", "hi-IN": "IFA टैबलेट" },
  vaccination_status: { "en-IN": "Vaccination", "ta-IN": "தடுப்பூசி", "hi-IN": "टीकाकरण" },
  next_visit_date: { "en-IN": "Next visit", "ta-IN": "அடுத்த வருகை", "hi-IN": "अगली विज़िट" },
  observations: { "en-IN": "Observations", "ta-IN": "குறிப்புகள்", "hi-IN": "टिप्पणियाँ" },
};

export const VISIT_TYPE_LABELS: Record<string, Dict> = {
  pregnancy_anc: { "en-IN": "Pregnancy (ANC)", "ta-IN": "கர்ப்பகால (ANC)", "hi-IN": "गर्भावस्था (ANC)" },
  newborn_hbnc: { "en-IN": "Newborn (HBNC)", "ta-IN": "புதிதாகப் பிறந்த குழந்தை", "hi-IN": "नवजात (HBNC)" },
  postnatal: { "en-IN": "Postnatal", "ta-IN": "பிரசவத்திற்குப் பின்", "hi-IN": "प्रसव के बाद" },
  immunization: { "en-IN": "Immunization", "ta-IN": "தடுப்பூசி", "hi-IN": "टीकाकरण" },
  family_planning: { "en-IN": "Family planning", "ta-IN": "குடும்பக் கட்டுப்பாடு", "hi-IN": "परिवार नियोजन" },
  general: { "en-IN": "General visit", "ta-IN": "பொதுவான வருகை", "hi-IN": "सामान्य विज़िट" },
};

/**
 * Danger labels are stored with the alert in the language used at detection
 * time. Re-localise by rule code so switching language later also switches the
 * alert, without touching the stored record.
 */
export const DANGER_LABELS: Record<string, Dict> = {
  vaginal_bleeding: {
    "en-IN": "Vaginal bleeding",
    "ta-IN": "பிறப்புறுப்பு இரத்தப்போக்கு",
    "hi-IN": "योनि से रक्तस्राव",
  },
  severe_headache: {
    "en-IN": "Severe headache or blurred vision",
    "ta-IN": "கடுமையான தலைவலி அல்லது மங்கலான பார்வை",
    "hi-IN": "तेज़ सिरदर्द या धुंधला दिखना",
  },
  convulsions: { "en-IN": "Convulsions / fits", "ta-IN": "வலிப்பு", "hi-IN": "दौरे / झटके" },
  high_fever: { "en-IN": "High fever", "ta-IN": "அதிக காய்ச்சல்", "hi-IN": "तेज़ बुखार" },
  reduced_fetal_movement: {
    "en-IN": "Reduced or absent baby movement",
    "ta-IN": "குழந்தையின் அசைவு குறைவு",
    "hi-IN": "शिशु की हलचल कम या बंद",
  },
  swelling: {
    "en-IN": "Swelling of face or hands",
    "ta-IN": "முகம் அல்லது கைகளில் வீக்கம்",
    "hi-IN": "चेहरे या हाथों में सूजन",
  },
  leaking_fluid: { "en-IN": "Leaking of fluid", "ta-IN": "நீர் இறங்குதல்", "hi-IN": "पानी का रिसाव" },
  severe_abdominal_pain: {
    "en-IN": "Severe abdominal pain",
    "ta-IN": "கடுமையான வயிற்று வலி",
    "hi-IN": "तेज़ पेट दर्द",
  },
  difficulty_breathing: {
    "en-IN": "Difficulty in breathing",
    "ta-IN": "மூச்சுத் திணறல்",
    "hi-IN": "साँस लेने में कठिनाई",
  },
  newborn_not_feeding: {
    "en-IN": "Not feeding / feeding poorly",
    "ta-IN": "பாலூட்ட மறுக்கிறது / சரியாக பால் குடிக்கவில்லை",
    "hi-IN": "दूध नहीं पी रहा / कम पी रहा",
  },
  newborn_low_temperature: {
    "en-IN": "Low body temperature",
    "ta-IN": "உடல் வெப்பநிலை குறைவு",
    "hi-IN": "शरीर का तापमान कम",
  },
  newborn_fast_breathing: { "en-IN": "Fast breathing", "ta-IN": "வேகமான மூச்சு", "hi-IN": "तेज़ साँस" },
  newborn_chest_indrawing: { "en-IN": "Chest indrawing", "ta-IN": "மார்பு உள்ளிழுத்தல்", "hi-IN": "छाती धँसना" },
  newborn_jaundice: {
    "en-IN": "Jaundice (yellow skin or eyes)",
    "ta-IN": "மஞ்சள் காமாலை",
    "hi-IN": "पीलिया",
  },
  newborn_umbilical_infection: {
    "en-IN": "Umbilical redness or pus",
    "ta-IN": "கொப்பூழில் சிவப்பு அல்லது சீழ்",
    "hi-IN": "नाभि में लाली या मवाद",
  },
  newborn_persistent_vomiting: {
    "en-IN": "Persistent vomiting / no urine",
    "ta-IN": "தொடர்ந்து வாந்தி / சிறுநீர் இல்லை",
    "hi-IN": "लगातार उल्टी / पेशाब नहीं",
  },
  postpartum_heavy_bleeding: {
    "en-IN": "Heavy bleeding after delivery",
    "ta-IN": "பிரசவத்திற்குப் பின் அதிக இரத்தப்போக்கு",
    "hi-IN": "प्रसव के बाद अधिक रक्तस्राव",
  },
  postpartum_infection: {
    "en-IN": "Foul-smelling discharge or fever after delivery",
    "ta-IN": "பிரசவத்திற்குப் பின் துர்நாற்றம் / காய்ச்சல்",
    "hi-IN": "प्रसव के बाद बदबूदार स्राव या बुखार",
  },
  low_birth_weight: {
    "en-IN": "Low birth weight (<2.5 kg)",
    "ta-IN": "குறைந்த பிறப்பு எடை (2.5 கிலோவுக்கும் குறைவு)",
    "hi-IN": "कम जन्म वज़न (2.5 किलो से कम)",
  },
};

export const FOLLOWUP_TITLES: Record<string, Dict> = {
  referral: {
    "en-IN": "URGENT: Refer to PHC today",
    "ta-IN": "அவசரம்: இன்றே PHC-க்கு அழைத்துச் செல்லுங்கள்",
    "hi-IN": "अत्यावश्यक: आज ही PHC ले जाएँ",
  },
  schedule_visit: {
    "en-IN": "Schedule next visit",
    "ta-IN": "அடுத்த வருகையைத் திட்டமிடுங்கள்",
    "hi-IN": "अगली विज़िट तय करें",
  },
  ifa: { "en-IN": "IFA follow-up", "ta-IN": "IFA தொடர் பரிசோதனை", "hi-IN": "IFA फ़ॉलो-अप" },
  vaccination: {
    "en-IN": "Verify vaccination status",
    "ta-IN": "தடுப்பூசி நிலையைச் சரிபார்க்கவும்",
    "hi-IN": "टीकाकरण स्थिति जाँचें",
  },
  anc: { "en-IN": "ANC checkup pending", "ta-IN": "ANC பரிசோதனை நிலுவை", "hi-IN": "ANC जाँच बाकी" },
  hbnc: {
    "en-IN": "Newborn danger-sign check (HBNC)",
    "ta-IN": "புதிதாகப் பிறந்த குழந்தையின் ஆபத்து அறிகுறி சோதனை (HBNC)",
    "hi-IN": "नवजात खतरे के संकेत जाँच (HBNC)",
  },
  next_visit: { "en-IN": "Next scheduled visit", "ta-IN": "அடுத்த திட்டமிட்ட வருகை", "hi-IN": "अगली निर्धारित विज़िट" },
  next_visit_pregnancy_anc: { "en-IN": "Next ANC checkup", "ta-IN": "அடுத்த ANC பரிசோதனை", "hi-IN": "अगली ANC जाँच" },
  next_visit_newborn_hbnc: { "en-IN": "Next newborn home visit", "ta-IN": "அடுத்த புதிதாகப் பிறந்த குழந்தை வீட்டு வருகை", "hi-IN": "अगली नवजात गृह भेंट" },
  next_visit_postnatal: { "en-IN": "Next postnatal checkup", "ta-IN": "அடுத்த பிரசவத்திற்குப் பின் பரிசோதனை", "hi-IN": "अगली प्रसव-पश्चात जाँच" },
  next_visit_immunization: { "en-IN": "Next immunization visit", "ta-IN": "அடுத்த தடுப்பூசி வருகை", "hi-IN": "अगली टीकाकरण विज़िट" },
  next_visit_family_planning: { "en-IN": "Next family planning visit", "ta-IN": "அடுத்த குடும்பக் கட்டுப்பாடு வருகை", "hi-IN": "अगली परिवार नियोजन विज़िट" },
  next_visit_general: { "en-IN": "Next general visit", "ta-IN": "அடுத்த பொதுவான வருகை", "hi-IN": "अगली सामान्य विज़िट" },
};

export function t(key: string, language: Language): string {
  return S[key]?.[language] ?? S[key]?.["en-IN"] ?? key;
}

export function tf(key: string, language: Language, values: Record<string, string | number>): string {
  return Object.entries(values).reduce(
    (text, [name, value]) => text.replaceAll(`{${name}}`, String(value)),
    t(key, language),
  );
}

export function fieldLabel(field: string, language: Language): string {
  return FIELD_LABELS[field]?.[language] ?? FIELD_LABELS[field]?.["en-IN"] ?? field.replace(/_/g, " ");
}

export function visitTypeLabel(value: string, language: Language): string {
  return VISIT_TYPE_LABELS[value]?.[language] ?? VISIT_TYPE_LABELS[value]?.["en-IN"] ?? value;
}

export const LANGUAGE_NAMES: Record<string, Dict> = {
  "en-IN": { "en-IN": "English", "ta-IN": "ஆங்கிலம்", "hi-IN": "अंग्रेज़ी" },
  "ta-IN": { "en-IN": "Tamil", "ta-IN": "தமிழ்", "hi-IN": "तमिल" },
  "hi-IN": { "en-IN": "Hindi", "ta-IN": "இந்தி", "hi-IN": "हिंदी" },
};

export function dangerLabel(hit: Pick<DangerHit, "code" | "label">, language: Language): string {
  return DANGER_LABELS[hit.code]?.[language] ?? hit.label;
}

export function languageName(code: string | null | undefined, language: Language): string {
  if (!code) return S.notSpecified[language];
  return LANGUAGE_NAMES[code]?.[language] ?? code;
}

export function followupTitle(task: FollowUp, language: Language): string {
  const key = task.title_key || "";
  return FOLLOWUP_TITLES[key]?.[language] ?? FOLLOWUP_TITLES[key]?.["en-IN"] ?? task.title;
}

export function followupWho(task: FollowUp, language: Language): string {
  return task.patient_name || task.beneficiary_id || t("beneficiaryGeneric", language);
}

export function followupDetail(task: FollowUp, language: Language): string {
  if (language === "en-IN") return task.detail;
  const who = followupWho(task, language);
  const key = task.title_key || "";
  if (key === "referral") return tf("detailReferral", language, { who });
  if (key === "schedule_visit") return tf("detailScheduleVisit", language, { who });
  if (key.startsWith("next_visit")) return tf("detailNextVisit", language, { who });
  if (key === "ifa") return tf("detailIFA", language, { who });
  if (key === "vaccination") {
    return task.detail.toLowerCase().includes("pending")
      ? tf("detailVaccinationDue", language, { who })
      : tf("detailVaccination", language, { who });
  }
  if (key === "anc") return tf("detailANC", language, { who });
  if (key === "hbnc") return tf("detailHBNC", language, { who });
  return task.detail;
}

export function visitDisplayName(visit: VisitSummary, language: Language): string {
  if (visit.patient_name) return visit.patient_name;
  if (visit.beneficiary_id) return visit.beneficiary_id;
  return visit.visit_type === "newborn_hbnc"
    ? t("babyNotNamed", language)
    : t("beneficiaryNotNamed", language);
}

export function extractionLabel(method: string | undefined, language: Language): string {
  if (method === "manual") return t("extractionManual", language);
  if (method === "llm") return t("extractionLlm", language);
  return t("extractionRules", language);
}
