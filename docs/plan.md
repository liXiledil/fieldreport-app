# FieldReport App: architecture and build plan (outside Copilot)

Goal: one cohesive app that turns a field engineer's raw job capture (voice notes, photos, TurboCell CSVs, receipts) into finished report content, chart summaries, and an expense package. It's built so it can serve Olan first and other field service engineers later.

Earlier context: [field-report-copilot-playbook.md](field-report-copilot-playbook.md) (the workflow this app automates).

## Ground rules

- **Data:** develop and demo with **synthetic job data**: made-up site, unit, readings, receipts, and a look-alike report template. No real company data goes into personal AI accounts unless your company approves it.
- **IP:** build on your own time and equipment, with no company templates or proprietary file formats copied in. Read your employment agreement's invention clause before selling anything.
- **Deployable inside a company:** the AI layer uses a swappable "model provider," so a company could later point it at its own approved setup (Azure OpenAI, Claude through AWS Bedrock or Google Vertex, or an enterprise Claude or ChatGPT account). This is what turns "you can't use that here" into "we can approve that."

## Which model does what

Using all three providers just for the sake of it adds cost and complexity. Each provider earns its place below, and every call sits behind one adapter so models can be swapped freely.

| Job | Best fit | Why |
|---|---|---|
| Report drafting from notes, multi-template output | **Claude** (Sonnet tier for daily use, Opus tier for hard cases) | Strong at long, structured, faithful technical writing and at following "don't invent" rules |
| Receipt and photo reading (vision → structured data) | **Claude** or **OpenAI** (whichever extracts receipts more accurately in testing) | Both are strong; benchmark on 30 sample receipts |
| Voice note transcription | **OpenAI** speech-to-text | Mature, cheap, handles noisy site audio and jargon well, with a custom vocabulary prompt |
| TurboCell CSV analysis | **Plain code (Python/pandas), not an LLM** | Min, max, spreads, and event detection must be exact; the LLM only writes the summary paragraph from the computed numbers |
| Verifier step ("Thirdgood") | A second, cheaper model call | Checks the draft against notes and data for invented values, missing sections, and policy and PII issues |
| Grok | Optional, not in the core path | Nothing in this workflow needs it; keep it as a fallback provider in the adapter, or use it for market research on X |

## Architecture

```
[Phone capture (PWA)]  voice | photos | receipts | CSV upload
        │
        ▼
[Job store]  one folder or database record per job (work order, site, dates)
        │
        ▼
[Processing pipeline]
  1. Transcribe voice notes (OpenAI STT)
  2. Extract receipts → JSON (vision model)
  3. Analyze TurboCell CSVs → stats + events (pandas) → summary (LLM)
  4. Caption and sort photos (vision model + timestamps)
  5. Draft report sections per template (Claude), using:
       - the template's "section map" (headings + field names)
       - style rules + example reports
  6. Verifier pass → [CONFIRM] flags + open-items list
        │
        ▼
[Review screen]  edit, approve each section, resolve [CONFIRM]s
        │
        ▼
[Outputs]
  - report-fields.json / .xlsx  → loaded into the macro template by a small VBA "Import" macro
    (the app never rewrites the macro template itself, so macros stay intact)
  - photo appendix (.docx or PDF)
  - expense sheet (CSV/XLSX) in Stars' field order + renamed receipt files
  - open items list
```

**Why fill macro templates with JSON plus VBA:** Python libraries can fill plain .docx templates easily, but they can damage macro-enabled .docm files. Exporting a fields file and having a 20-line VBA macro pull it into bookmarks or content controls keeps every company's template untouched. That works for any customer, which is a selling point.

**Stars and other expense portals:** start with the entry sheet plus renamed receipts. Later, an optional browser extension could autofill the Stars form from the sheet, but only with company approval.

## Tech stack (simple, cheap, and Claude Code can build it)

- **Backend:** Python with FastAPI. Uses pandas for CSV work, the Anthropic and OpenAI SDKs behind one `ModelProvider` interface, and openpyxl and python-docx for outputs.
- **Frontend:** a Next.js PWA, installable on a phone, offline-friendly capture that syncs later (sites often have poor signal).
- **Storage:** SQLite and local files for v1; Postgres and S3 when multi-user.
- **Hosting:** run it on your laptop for v1; one small cloud server for pilots.
- **Cost:** a few dollars of API usage per job at most at the Sonnet tier. Budget to confirm during testing.

## Build phases

| Phase | What | Result |
|---|---|---|
| 0. Repo + sample data (1 to 2 days) | Create a GitHub repo; generate a synthetic job (notes, 30 receipts, TurboCell-style CSV, a sample report template + section map) | Something safe to build and demo against |
| 1. Pipeline MVP (1 to 2 weeks) | Command-line or simple web app: job folder in, report fields + expense sheet + CSV summary + open items out | Proves the core value |
| 2. Template import macro | VBA macro that loads report-fields.json into a .docm template | Works with real macro templates |
| 3. Review UI + verifier | Section-by-section approval, [CONFIRM] resolution | Engineer stays in control |
| 4. Mobile capture PWA | Voice, photo, and receipt capture on site, synced to the job | The "capture as you go" habit, built in |
| 5. Pilot | 3 to 5 field service engineers (other companies or contractors) on their own data | Evidence for a business |

## Business angle

- **Who it's for:** field service engineers on gas turbines, steam turbines, compressors, wind, and other rotating equipment, at OEMs and independent service providers.
- **What sets it apart:** engineering-grade technical reports from raw site data that fill the customer's own template, plus a built-in no-invention verifier. Generic field-service form apps don't do this.
- **Pricing to test:** $30 to $60 per engineer per month for individuals and small shops; company licenses deployed on the customer's own approved AI.
- **Next validation step:** talk to 5 fellow engineers about their admin hours per job and whether they'd pay.

## What I need to start building

1. Your choice on the policy question (product on sample data, personal tool after approval, or both).
2. A GitHub repo for it. Create an empty one, for example `fieldreport-app`, and tell me the name. I can't create repos myself.
3. Generic versions of your report section headings (no company content), so the sample template is realistic.
