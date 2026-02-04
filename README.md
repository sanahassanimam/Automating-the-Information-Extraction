# Automating-the-Information-Extraction

A lightweight, research-oriented toolkit for (1) discovering relevant scientific papers and (2) extracting structured information from PDFs using evidence-based heuristics and an optional local LLM (Ollama).

This repository contains two modules:

- **paper-finder**: a browser-based paper search interface for OpenAlex, PubMed, and arXiv with CSV export
- **info-extractor**: a local web app (FastAPI backend + HTML frontend) for schema-driven extraction from PDF URL uploads or local PDFs

The goal is to support transparent, reproducible data extraction workflows for evidence synthesis and meta-research.

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


> Folder names use hyphens to avoid space-related path issues on Windows and in scripts.

---

## 1) Paper Finder (OpenAlex + PubMed + arXiv)

### What it does
`paper-finder/search.html` provides a simple UI to:
- search **OpenAlex**, **PubMed**, and **arXiv**
- filter by publication year and per-source result limits
- optionally restrict OpenAlex to **open-access**
- select results and **export selected papers to CSV**
- open available PDF links (OA PDFs when available)

### How to run
This is a static HTML file.

**Option A (quickest):** open in browser  
Double-click `paper-finder/search.html`.

**Option B (recommended): serve locally**
From the repo root:

```bash
cd paper-finder
python -m http.server 5174
Open:

http://127.0.0.1:5174/search.html
2) Info Extractor (FastAPI + HTML frontend + optional Ollama)
What it does
info-extractor extracts structured fields from PDFs in a schema-driven way:

You define fields (e.g., title, authors[], sample_size, TR, TE)

The frontend generates a JSON Schema automatically

The backend extracts:

heuristics (regex + evidence snippets) for key technical fields

optionally uses a local LLM via Ollama to fill missing fields

The app returns:

extracted JSON

evidence contexts for heuristic hits

schema validation results

a one-row CSV download for quick export

Requirements
Python 3.9+ recommended

Conda environment (as used in your workflow): paperextract

Dependencies typically include:

fastapi, uvicorn, httpx, pymupdf (fitz), jsonschema

If you add a requirements.txt later, include these packages for reproducibility.

How to run (quick checklist)
Terminal 1 — Ollama (optional, only if using local LLM)
ollama serve
If Ollama is already running, you can skip this.

Terminal 2 — Backend (FastAPI)
cd "C:\Users\imam\Documents\paper-extractor\info-extractor\backend"
conda activate paperextract
uvicorn server:app --reload --port 8000
Backend runs at:

http://127.0.0.1:8000
API docs:

http://127.0.0.1:8000/docs
Terminal 3 — Frontend server (static HTML)
cd "C:\Users\imam\Documents\paper-extractor\info-extractor\frontend"
python -m http.server 5173
Open the UI:

http://127.0.0.1:5173/extractor_ui.html
Using the extractor UI
Provide a PDF URL (open access preferred) or upload a PDF file

Provide a field list (one per line), e.g.

title

authors[]

year

doi

sample_size

TR

TE

scanner

smoothing

Click Generate schema (or keep auto-generate on)

Click Extract

Optional: tick Use local LLM (Ollama)

Download a one-row CSV from the extracted JSON output

Notes on Open Access and PDFs
Paper Finder will only open/export PDF links when an OA PDF link is available.

PubMed OA detection is limited in the current MVP (OA is treated as unknown in PubMed mode).

For extraction, uploads are the most reliable because some PDF URLs block automated downloads.

Data and reproducibility
Recommended practice:

Do not commit large PDFs, extracted datasets, or private materials to GitHub.

Keep raw PDFs locally and commit only code, schemas, and small demo outputs.

License
See LICENSE in this repository.

Contact
Maintainer: Sana Hassan Imam
GitHub: sanahassanimam

