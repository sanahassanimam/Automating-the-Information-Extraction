# Automating-the-Information-Extraction

This repository contains two **separate** tools:

1. **Paper Finder** — helps you **find and shortlist papers** from multiple scholarly platforms (OpenAlex, PubMed, arXiv) and export the results.
2. **Info Extractor** — helps you **extract structured information from a specific paper (PDF)** by uploading it (or providing a URL) and defining a custom schema; extraction is done via **heuristics** and optionally a **local LLM (Ollama)**.

The tools are intentionally decoupled: Paper Finder supports *paper discovery*, while Info Extractor supports *paper-level structured data extraction*.

---

## Repository structure

Automating-the-Information-Extraction/
├── paper-finder/
│ └── search.html
└── info-extractor/
├── backend/
│ └── server.py
└── frontend/
└── extractor_ui.html


---

## 1) Paper Finder (OpenAlex + PubMed + arXiv)

### Purpose
Paper Finder is a lightweight browser UI for **searching and collecting candidate papers** across:
- **OpenAlex**
- **PubMed**
- **arXiv**

It is designed for quickly building a shortlist that you can later screen or feed into downstream extraction.

### Key features
- Query-based search with **year range** filtering
- Adjustable **max results per source**
- Source selection (enable/disable OpenAlex/PubMed/arXiv)
- **OpenAlex open-access-only** filter (optional)
- Manual selection of papers
- Export selected papers to **CSV**
- Open available **PDF links** (where present)

### Run Paper Finder
Paper Finder is a **static HTML file**.

**Option A (simplest):**
- Open `paper-finder/search.html` directly in your browser (double-click).

**Option B (recommended): serve locally**
```bash
cd paper-finder
python -m http.server 5174

Open:
http://127.0.0.1:5174/search.html

Notes / limitations

OpenAlex can provide OA PDF links when available.

PubMed results link to PubMed landing pages; OA detection is limited in this MVP.

arXiv is open by default and typically provides direct PDF links.

2) Info Extractor (PDF Upload/URL → Schema-driven extraction)
Purpose

Info Extractor is a paper-level information extraction tool:

You upload a PDF (or provide a PDF URL),

specify what fields you want to extract (schema),

and the system returns structured output as JSON (plus downloadable CSV).

It supports two extraction modes:

Heuristics mode (default): regex-based extraction with evidence snippets (fast, transparent)

LLM mode (optional): uses a local Ollama model to fill fields according to a JSON schema, with heuristics used as evidence-based fallback for missing/null values

Key features

Upload PDF or provide PDF URL

Define extraction targets using Fields (one per line) (e.g., title, authors[], sample_size, TR)

Auto-generates JSON Schema from your field list

(Optional) Convert a natural-language request into a field list using Ollama

Extraction output includes:

extracted_json (final structured output)

evidence (heuristic matches + context)

validation_errors (JSON Schema validation)

backend notes (mode used, merge policy, etc.)

One-click Download CSV (single-row export from extracted JSON)

How to run Info Extractor (Windows, local)
Terminal 1 — Ollama (optional, only if using local LLM)

How to run Info Extractor (Windows, local)
Terminal 1 — Ollama (optional, only if using local LLM)
ollama serve


If Ollama is already running, skip this.

Terminal 2 — Backend (FastAPI)
cd "C:\Users\imam\Documents\paper-extractor\info-extractor\backend"
conda activate paperextract
uvicorn server:app --reload --port 8000


Backend:

API root: http://127.0.0.1:8000

Swagger docs: http://127.0.0.1:8000/docs

Terminal 3 — Frontend server (static HTML)
cd "C:\Users\imam\Documents\paper-extractor\info-extractor\frontend"
python -m http.server 5173


Open:

http://127.0.0.1:5173/extractor_ui.html

Using the Info Extractor UI (typical workflow)

Provide a PDF:

PDF URL (open-access preferred), or

Upload a local PDF (most reliable)

Define fields to extract (one per line), e.g.

title

authors[]

year

doi

sample_size

TR

TE

scanner

smoothing

Click Generate schema (or keep auto-generate enabled)

Click Extract

Default = heuristics

Optional: tick Use local LLM (Ollama) and choose model + number of pages sent to the LLM

Review:

Extracted JSON

Evidence snippets (heuristics)

Validation errors (if any)

Click Download CSV to export a single-row CSV

Extraction behavior (important)

Heuristics provide evidence-based matches for selected fields (e.g., sample_size, TR, TE, scanner strength, smoothing).

If LLM extraction is enabled:

The LLM is asked to output JSON matching the schema.

The final output follows the policy:

LLM first

then fill missing/null values from heuristics when available (evidence-based)

Recommended practice (data + reproducibility)

Avoid committing large PDFs or private datasets to GitHub.

Keep PDFs locally in a non-tracked folder (e.g., data/) and commit only code and small demo artifacts.

License

See the LICENSE file in this repository.

Contact

Maintainer: Sana Hassan Imam
GitHub: sanahassanimam
