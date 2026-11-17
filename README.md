# ASHA VoiceCare

A mobile-first voice agent for ASHA workers. The worker speaks a home-visit note
in their own language; the app streams the speech through Gnani's speech APIs,
builds a structured visit record, reads it back for confirmation, raises a
guideline-based danger-sign alert when needed, and creates follow-up tasks
automatically.

> **Prototype status.** Hackathon build, not a medical device. It does **not**
> diagnose, prescribe or recommend treatment. Every record requires the
> worker's spoken confirmation before it is saved. Use synthetic beneficiaries
> only — never enter real patient data.

---

## The five required modules

| Requirement | How it is implemented | Main code |
| --- | --- | --- |
| 1. Streaming speech-to-text (not record-then-upload) | The browser streams 512-sample PCM frames over a WebSocket. FastAPI proxies them to Gnani Prisma v3.0, returns live interim text every ~450 ms, then a final transcript per utterance. | `frontend/src/audio.ts`, `backend/app/gnani.py`, `backend/app/session.py` |
| 2. AI-built structured record | Deterministic rule extractor turns the transcript into a `VisitRecord`: beneficiary ID, name, visit type, weight, ANC/IFA status, vaccination, next visit, observations. Missing fields stay `null` and are surfaced as questions — nothing is invented. An optional OpenAI-compatible LLM adapter can be enabled, but its output is validated and falls back to rules. | `backend/app/extract.py`, `backend/app/normalize.py` |
| 3. Spoken confirmation and correction (with barge-in) | The record is read back with Gnani Timbral TTS. The worker can interrupt mid-sentence (client-side RMS barge-in), say "No, weight is 2.8 kilo", and the parser maps the utterance to exactly one field before re-reading it. | `backend/app/dialog.py`, `frontend/src/audio.ts`, `frontend/src/App.tsx` |
| 4. Danger-sign detection + PHC referral | A fixed, guideline-derived rule engine runs **independently of the LLM**. It is negation-aware ("no bleeding", "bleeding illa" do not alert), infers mother vs newborn subject, speaks an alarm immediately, and creates an urgent "refer to PHC today" task. | `backend/app/danger.py`, `backend/app/followups.py` |
| 5. Automatic follow-up list | Each confirmed visit produces scheduled tasks: next visit, IFA compliance, vaccination gaps, ANC gaps, newborn HBNC checks, and emergency referrals. Tasks have due dates, priorities and completion status. | `backend/app/followups.py`, `backend/app/db.py`, `frontend/src/components/FollowUpList.tsx` |

---

## Architecture

```
┌──────────────────────────── Browser (React + Tailwind) ───────────────────────────┐
│  Mic → AudioWorklet (512 samples / 1024 bytes) ──► WebSocket /ws/visit            │
│  Speaker ◄── WAV from /api/tts ◄── JSON "speak" events                            │
└──────────────────────────────────────┬────────────────────────────────────────────┘
                                       │ PCM frames + JSON commands
                                       ▼
┌──────────────────────────── FastAPI (backend/app) ────────────────────────────────┐
│  VisitSession state machine: idle → recording → finalising → review → saved       │
│       │                    │                    │                                 │
│       │ audio              │ final transcript   │ confirm/correct                 │
│       ▼                    ▼                    ▼                                 │
│  Gnani STT v3        rules extractor       correction parser                      │
│  (server-side key)         │                    │                                 │
│                            ▼                    ▼                                 │
│                     danger rule engine ──► follow-up planner ──► SQLite           │
└────────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
                          Gnani TTS (Shivani, timbre-v3.0)
```

Why the STT WebSocket is proxied by the backend:

- Browsers cannot set the `x-api-key-id` upgrade header, so the Gnani key never
  reaches the client.
- One persistent Gnani stream is kept for the whole visit, which is what makes
  barge-in and correction possible without a reconnect.
- The backend re-chunks any browser payload into exact 1024-byte frames, so the
  audio contract is enforced in one place.

---

## Quick start

Requirements: Python 3.11+, Node 20+, a Gnani API key.

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy ..\.env.example .env
# edit .env and set GNANI_API_KEY
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

On macOS/Linux use `source .venv/bin/activate` and `uvicorn app.main:app ...`.

Health check: <http://127.0.0.1:8000/api/health> should report
`"gnani_configured": true`.

### 2. Frontend

Development (hot reload, proxies `/api` and `/ws` to port 8000):

```powershell
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. For a production build:

```powershell
npm run build
```

FastAPI automatically serves `frontend/dist` at <http://127.0.0.1:8000/> when
that directory exists, so the whole demo can run from one process.

> **Secret hygiene:** `backend/.env` is gitignored. The development key used to
> build this prototype should be rotated after the hackathon.

### Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `GNANI_API_KEY` | — | Required for streaming STT and TTS |
| `GNANI_STT_MODEL` | `prisma-v3.0` | Gnani streaming ASR model |
| `GNANI_TTS_MODEL` | `timbre-v3.0` | Gnani speech synthesis model |
| `GNANI_TTS_VOICE` | `Shivani` | Warm, empathetic voice; works across the supported languages |
| `LLM_BASE_URL` | empty | Optional OpenAI-compatible endpoint |
| `LLM_API_KEY` | empty | Optional LLM key |
| `LLM_MODEL` | empty | Optional model name; rules are used when empty |
| `DATABASE_PATH` | `./data/asha.db` | SQLite path, relative to `backend/` |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | CORS origin for the Vite dev server |

The template is at [`.env.example`](.env.example).

### Deploying a live demo

Voice needs the long-running FastAPI process (WebSocket + server-side key), so a
static host such as GitHub Pages cannot run this app by itself. The app must be
deployed to a container/VM host, and the key must be set as a **server
environment variable** there:

- **Never commit `backend/.env` or put the key in `VITE_*` variables.** Vite
  bakes those into the public JavaScript bundle.
- The backend reads `GNANI_API_KEY` from the process environment first; a local
  `backend/.env` is only a development fallback.
- After deploying, open `/api/health` and confirm `"gnani_configured": true`.
  If it is false, the process cannot see the variable — set it in the host's
  dashboard and redeploy/restart.

**Docker (any host):**

```powershell
docker build -t asha-voicecare .
docker run --rm -p 8000:8000 `
  -e GNANI_API_KEY="<your-gnani-key>" `
  -v asha-data:/data `
  -e DATABASE_PATH=/data/asha.db `
  asha-voicecare
```

Open <http://localhost:8000>. Do not copy the key into an image layer or a
committed file.

**Render (one-click blueprint):**

1. Create a new **Blueprint** in Render and select this repository. Render reads
   [`render.yaml`](render.yaml).
2. When prompted for `GNANI_API_KEY`, paste the key. Render stores it as a secret
   and injects it at runtime.
3. Deploy, then check `https://<service>.onrender.com/api/health` for
   `"gnani_configured": true`.

The free blueprint uses `/tmp/asha.db`, so demo records reset when the instance
restarts. Attach a persistent disk and set `DATABASE_PATH=/data/asha.db` if that
matters. The database starts empty; seed the synthetic demo through the host's
shell:

```powershell
cd backend
.\.venv\Scripts\python.exe tools\seed_demo_data.py
```

On Render, use the service **Shell** and run `python tools/seed_demo_data.py`
from `backend/`.

**Split frontend/backend:** build the frontend with
`VITE_API_BASE=https://your-backend.example.com`, and set the backend's
`FRONTEND_ORIGIN` to the frontend origin so REST CORS and the WebSocket both
work. Keeping both behind one origin, as the Dockerfile does, avoids this.

---

## Demo script

All names and IDs below are fictional.

### Demo 1 — normal pregnancy visit

Tap the microphone and say:

> "Lakshmi, beneficiary ID ASHA102. Pregnancy visit. Weight 55 kilo.
> ANC completed. IFA tablets given. Next visit November 20."

Expected results:

- Record: Lakshmi / ASHA102 / pregnancy ANC / 55 kg / ANC completed /
  IFA provided / next visit 20 November.
- Read-back is spoken; tap **Confirm & save** (or say "yes").
- Follow-ups: next ANC checkup, IFA follow-up, verify vaccination status.

### Demo 2 — newborn danger sign

Say:

> "Newborn has high fever. Weight 2.8 kilo."

Expected results:

- An alarm appears and is spoken **during** dictation, as soon as "high fever"
  is recognised.
- The record remains a draft: the missing beneficiary ID, name and next visit
  date are asked for, not invented.
- An urgent "Refer to PHC today" task is created first in the follow-up list.

### Demo 3 — barge-in correction

Say:

> "Weight is 2.5 kilo."

While the read-back is speaking, interrupt with:

> "No, weight is 2.8 kilo."

Expected results:

- Playback stops immediately (client RMS barge-in).
- Only the weight changes; the next-visit date is untouched.
- The app speaks "I have corrected the weight to 2.8 kilograms."
- Confirm to save the corrected value.

A typed-input fallback is available inside the recording screen ("Type
instead · demo fallback") for noisy venues where the microphone fails. It
injects text into the same pipeline, so the rest of the behaviour is identical.

---

## How the record is kept honest

- **No invention.** Fields that were not spoken remain `null`. `VisitRecord.missing()`
  asks for beneficiary ID, name, weight (for maternal/newborn visits) and the
  next visit date before saving.
- **Confidence is shown, not hidden.** A low-confidence value is displayed with
  a "Please confirm" badge; it is never silently accepted as fact.
- **Corrections are evidence-tracked.** Each voice correction is stored with
  the field, new value, original utterance and date.
- **The LLM cannot override the safety rules.** Danger detection runs on the
  transcript with a separate deterministic engine. Even when an LLM extractor is
  enabled, it only fills structured fields and is validated against the rules
  fallback.
- **No diagnosis or treatment advice.** The only clinical output is a referral
  instruction derived from the fixed danger-sign list.

### Structured fields

`beneficiary_id`, `patient_name`, `visit_type`, `weight_kg`, `bp`,
`anc_completed`, `ifa_provided`, `vaccination_status`, `vaccines_due`,
`next_visit_date`, `observations`, plus language, transcript, confidence and
evidence maps.

Visit types: `pregnancy_anc`, `newborn_hbnc`, `postnatal`, `immunization`,
`family_planning`, `general`.

---

## Danger-sign engine

`backend/app/danger.py` contains 18 fixed text rules plus one numeric rule
(low birth weight < 2.5 kg). Each rule has a code, subject (`mother`, `newborn`
or `any`), English/Tamil/Hindi labels, regex patterns, urgency and a guideline
source string.

Safety properties:

- **Independent of the LLM.** No model call is involved in detecting danger.
- **Negation-aware.** A match is skipped when a negation marker appears in the
  same clause before it ("no bleeding", "she denies fever") or immediately after
  it ("bleeding illa", "fever नहीं"). Clause breaks at punctuation and
  "but/however" prevent a negation from leaking across sentences.
- **Subject-aware.** "Baby is not feeding" maps to the newborn category, while
  "mother has fever" maps to pregnancy/postpartum, using cue words near the match.
- **Never drops an alert silently.** Once a danger sign is detected in a visit,
  it stays in the record. Saying "no bleeding" can retract a false positive
  explicitly, but later text cannot erase an alert by omission.
- **Referral only.** The engine does not name a diagnosis or a medicine. The
  spoken output is a warning plus "refer to the nearest Primary Health Centre".

### Guideline citation block

> **Page-number policy.** This prototype cites guideline **sections**. Page
> numbers are deliberately **not guessed**. Before submitting or publishing,
> transcribe the exact page ranges from the printed/PDF copies into the table
> below and replace the "pending verification" entries. Version/year and section
> titles are the anchors the rules were written against.

| ID | Source and version | Sections used | Rules derived | Pages |
| --- | --- | --- | --- | --- |
| G1 | Ministry of Health and Family Welfare (MoHFW), Government of India — *Guidelines for Antenatal Care and Skilled Attendance at Birth by ANMs/LHVs/SNs*, **2010** | "Danger signs during pregnancy"; referral guidance | vaginal bleeding; severe headache/blurred vision; convulsions; high fever; reduced/absent fetal movement; swelling of face/hands; leaking fluid; severe abdominal pain; difficulty breathing | **Pending verification** — do not cite a page number until checked against the source |
| G2 | MoHFW / National Health Systems Resource Centre (NHSRC) — *Home Based Newborn Care (HBNC) Operational Guide*, **2014** | "Newborn danger signs"; low birth weight; referral | not feeding/poor feeding; low body temperature; fast breathing; chest indrawing; jaundice; umbilical redness/pus; persistent vomiting/no urine; low birth weight (<2.5 kg) | **Pending verification** |
| G3 | MoHFW — *ASHA Module 6: "Skills that Save Lives"* (ASHA training modules) | Postpartum danger signs; recognition and referral | heavy bleeding after delivery; foul-smelling discharge or fever after delivery | **Pending verification** — confirm the edition/year from the copy used |

These are the sources recorded on every `DangerHit.source` field (for example
`G1 §Danger signs during pregnancy; G3`), so an auditor can trace an alert back
to the guideline family. The exact page ranges still need a human check against
the official copies; this README intentionally does not fabricate them.

---

## Follow-up generation

For every confirmed visit, `build_followups()` deterministically creates:

1. **Urgent referral** — due today, priority `urgent`, when any danger sign is
   present. Always the first task.
2. **Next visit** — due on the spoken date; if no date was recorded, a
   high-priority "Schedule next visit" task is created instead.
3. **IFA follow-up** — when IFA tablets were provided.
4. **Verify vaccination status** — when vaccination was not recorded or is due.
5. **ANC checkup pending** — when a pregnancy visit did not confirm ANC completion.
6. **Newborn danger-sign check (HBNC)** — for every newborn visit, due in 3 days.

Tasks are stored in SQLite and can be marked done from the UI. The home screen
surfaces counts and urgent referrals.

---

## API and WebSocket protocol

### REST

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Service and credential status |
| `GET` | `/api/config` | Supported languages |
| `POST` | `/api/tts` | Text → WAV proxy (key stays server-side) |
| `GET` | `/api/visits?limit=30` | Recent visits |
| `GET` | `/api/visits/{id}` | One visit with follow-ups and alerts |
| `GET` | `/api/followups?status=pending` | Follow-up list |
| `POST` | `/api/followups/{id}/complete` | Mark a task done |
| `GET` | `/api/stats` | Dashboard counts |

### WebSocket `/ws/visit?language=en-IN`

Client → server:

- binary PCM frames (512 samples, 16-bit LE mono; the backend re-chunks)
- `{"type":"start","language":"en-IN","sample_rate":16000}`
- `{"type":"stop"}` — finish dictation and build the draft
- `{"type":"barge_in"}` — flush the open utterance after local playback stops
- `{"type":"confirm"}` — save the reviewed record
- `{"type":"cancel"}` — discard the visit
- `{"type":"inject","text":"…"}` — demo fallback; same pipeline as a transcript
- `{"type":"ping"}`

Server → client:

- `ready`, `recording`, `stt_connected`
- `partial` — interim text and/or the accumulated transcript plus a live record preview
- `alarm` — danger hits and the localised warning to speak
- `draft` — record, missing/unclear fields, danger, follow-ups and read-back text
- `speak` — text + language for the client to fetch from `/api/tts`
- `stop_audio`, `saved`, `error`, `pong`

---

## Data storage

The prototype uses SQLite via the Python standard library (no ORM):

- `beneficiaries` — synthetic beneficiary identity
- `visits` — structured fields, raw transcript, extracted JSON, corrections,
  danger JSON and extraction method
- `danger_alerts` — one row per detected sign, with guideline source and
  referral status
- `followups` — tasks with due date, priority, reason and completion

[`supabase_schema.sql`](supabase_schema.sql) mirrors the same design for a hosted
Postgres/Supabase demo. It is provided for migration; the running app uses
SQLite. Audio is **not** persisted — only transcripts and structured records.

---

## Testing

```powershell
cd backend
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

The suite covers normalisation (including real ASR artefacts), date/weight
parsing, extraction, absence of invented fields, danger rules and negation,
corrections (including the decimal-vs-date regression), follow-up generation,
and read-back wording in English and Tamil.

End-to-end scripts (the server must be running on port 8000):

```powershell
.\.venv\Scripts\python.exe tools\e2e_ws.py normal
.\.venv\Scripts\python.exe tools\e2e_ws.py danger
.\.venv\Scripts\python.exe tools\e2e_ws.py correction
.\.venv\Scripts\python.exe tools\e2e_audio.py   # real streaming STT; needs data/sample_visit.wav
```

`tools/smoke_gnani.py` regenerates the demo WAV with TTS and checks the REST STT
loopback. `tools/probe_partials.py` documents how live interim transcripts were
discovered.

> On PowerShell, unittest writes its summary to stderr, so the shell may report
> exit code 1 even when the last line says `OK`. Check for `OK` in the output.

---

## Gnani integration notes

- **Endpoints:** streaming STT
  `wss://api.vachana.ai/stt/v3/stream`; TTS
  `https://api.vachana.ai/api/v1/tts/inference`.
- **Auth:** `x-api-key-id` (STT upgrade header) and `X-API-Key-ID` (REST TTS).
- **Audio contract:** 512 samples / 1024 bytes per frame, 16-bit little-endian
  mono. The browser's native sample rate is declared in `x-sample-rate`; no
  client-side resampling is required.
- **Interim transcripts:** the live service advertises
  `partials_enabled: false` unless the otherwise-undocumented header
  `x-partials: true` is sent. With it, `partial_transcript` frames arrive about
  every 450 ms. This was found empirically with `tools/probe_partials.py` and
  drives the live word-by-word UI.
- **Final frames:** Gnani v3 emits `final_transcript`, not `transcript`; the
  backend normalises this to an internal `transcript` event.
- **Keyterms bias:** passing an `ANC`/`IFA`/`ASHA` term list fixes real ASR
  errors such as `ASHAH 102 → ASHA 102`, `"Hence he completed" → ANC completed`
  and `Tifa → IFA`. Medical vocabulary is also repaired in `normalize.py`.
- **Cloudflare:** `api.vachana.ai` returns error 1010 for Python's default
  urllib user agent, so every REST call sends a descriptive `User-Agent`.
- **Voice:** `Shivani` with `timbre-v3.0`, chosen for its warm healthcare
  persona and coverage of the supported languages.
- **Languages:** Gnani supports ten Indian languages; the demo UI wires
  English, Tamil and Hindi.

---

## Repository layout

```
asha-voicecare/
├── backend/
│   ├── app/
│   │   ├── main.py        FastAPI app, REST + WebSocket
│   │   ├── session.py     visit state machine, alarms, corrections, save
│   │   ├── gnani.py       streaming STT client and TTS client
│   │   ├── extract.py     rule extractor + optional LLM adapter
│   │   ├── normalize.py   code-mixed ASR repair, dates, weights, intents
│   │   ├── danger.py      deterministic danger-sign engine
│   │   ├── followups.py   automatic task generation
│   │   ├── dialog.py      read-back and correction parsing
│   │   ├── db.py          SQLite persistence
│   │   └── i18n.py        spoken strings, labels, warnings
│   ├── tests/             40 unit tests
│   ├── tools/             E2E, audio, smoke and probe scripts
│   └── data/              generated SQLite DB and demo WAV (gitignored)
├── frontend/
│   └── src/               React screens, audio worklet, strings, API client
├── supabase_schema.sql    hosted Postgres schema
├── Dockerfile             one-container live deployment
├── render.yaml            Render blueprint (prompts for the secret key)
├── .env.example
└── README.md
```

---

## Known limitations and next steps

- The rule extractor is tuned to the demo vocabulary and common code-mixed
  phrasing. Unusual sentence structures can leave fields missing; the app then
  asks rather than guessing. A production build should add more local-language
  evaluation data.
- Only three UI languages are wired (of Gnani's ten).
- SQLite is single-node and has no authentication. The Supabase schema is ready
  but the repository layer is not yet switched over.
- Barge-in uses a simple RMS threshold. Very noisy environments may need
  per-device calibration or server-side VAD.
- STT/TTS require network connectivity. There is no offline model.
- Guideline page numbers remain unverified (see the citation block). This is a
  deliberate anti-fabrication placeholder, not an oversight.
- The app creates a referral task but does not integrate with PHC systems,
  SMS/IVR escalation, or ambulance dispatch.
- The typed-input fallback is for demos, not for production record entry.

---

## Safety and data notice

This repository uses **synthetic beneficiaries only**. Names such as "Lakshmi"
and IDs such as `ASHA102` are fictional. Do not enter real patient information
into the prototype. The app does not diagnose, prescribe, or replace clinical
judgement; it only records what the worker said, reads it back, and follows a
fixed government guideline checklist to prompt referral.
