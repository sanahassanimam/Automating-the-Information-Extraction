# Automating-the-Information-Extraction

This repository contains **two independent but complementary tools** for academic workflows:

- **Paper Finder** — for *discovering and shortlisting* relevant research papers from multiple scholarly platforms.
- **Info Extractor** — for *extracting structured information* from a **specific paper (PDF)** based on a user-defined schema, using heuristics and optionally a local LLM (Ollama).

The tools are deliberately separated:
- **Paper Finder** answers *“Which papers should I look at?”*
- **Info Extractor** answers *“What information can I extract from this paper?”*

---

## Repository Structure

Automating-the-Information-Extraction/

├── paper-finder/

│   └── search.html

└── info-extractor/

    ├── backend/
    
    │   └── server.py
    
    └── frontend/
    
        └── extractor_ui.html

---

## 1. Paper Finder

### Purpose
Paper Finder is a browser-based tool for **retrieving and shortlisting academic papers** from multiple sources.  
It supports rapid exploration and export of candidate papers for later screening or analysis.

### Supported Platforms
- OpenAlex  
- PubMed  
- arXiv  

### Key Features
- Keyword-based search  
- Publication year range filtering  
- Per-source result limits  
- Enable/disable individual sources  
- Optional open-access-only filtering (OpenAlex)  
- Manual paper selection  
- Export selected papers to CSV  
- Open available PDF links (OA PDFs when available)

### How to Run
Paper Finder is a **static HTML application**.

Option A — Open directly  
- Double-click `paper-finder/search.html`

Option B — Serve locally (recommended)

cd paper-finder  
python -m http.server 5174  

Open in browser:

http://127.0.0.1:5174/search.html

### Notes
- OpenAlex may provide direct open-access PDF links.
- PubMed results link to PubMed landing pages; OA detection is limited in this MVP.
- arXiv papers are open by default and usually include direct PDF links.
- Paper Finder does not download or parse PDFs; it only helps identify and shortlist relevant papers.

---

## 2. Info Extractor

### Purpose
Info Extractor is a **paper-level information extraction tool**.

You provide:
- a PDF (uploaded locally or via URL)
- a schema describing what to extract

The system returns structured output in JSON and CSV formats.

---

## Extraction Modes

### Heuristics-Based Extraction (Default)
- Regex-based  
- Evidence-driven  
- Transparent and fast  
- Suitable for technical metadata (e.g., sample_size, TR, TE)

### LLM-Assisted Extraction (Optional)
- Uses a local Ollama model  
- Constrained by a JSON Schema  
- Heuristics fill missing or null values  
- No external API calls  

---

## Key Features
- PDF upload or PDF URL input  
- User-defined extraction fields (one field per line)  
- Automatic JSON Schema generation  
- Optional field generation from natural-language prompts  
- Evidence snippets for heuristic matches  
- JSON Schema validation  
- One-click CSV export (single-row output)

---

## How to Run Info Extractor (Local / Windows)

Terminal 1 — Ollama (Optional)

ollama serve

Terminal 2 — Backend (FastAPI)

cd C:\Users\imam\Documents\paper-extractor\info-extractor\backend  
conda activate paperextract  
uvicorn server:app --reload --port 8000  

API root:  
http://127.0.0.1:8000  

API documentation:  
http://127.0.0.1:8000/docs  

Terminal 3 — Frontend (HTML UI)

cd C:\Users\imam\Documents\paper-extractor\info-extractor\frontend  
python -m http.server 5173  

Open in browser:

http://127.0.0.1:5173/extractor_ui.html

---

## Typical Info Extractor Workflow
1. Provide a paper (PDF URL or local upload)
2. Define extraction fields (one per line)
3. Generate the schema
4. Click Extract
5. Review extracted JSON, evidence, and validation output
6. Download the CSV output

---
## **Workflow Overview**

![Automating the Information Extraction workflow](images/workflow.png)

## Extraction Logic
- Heuristics provide evidence-backed values whenever possible.
- If LLM extraction is enabled, LLM output is applied first.
- Missing or null fields are filled using heuristics.
- Final output always conforms to the generated JSON Schema.

---

## Data and Reproducibility Notes
- Do not commit large PDFs or private datasets to GitHub.
- Keep PDFs locally (e.g., in a non-tracked data directory).
- Commit only code, schemas, and small example outputs.

---

## License
See the LICENSE file in this repository.

---

## Contact
Sana Hassan Imam  
GitHub: sanahassanimam
Email:sana.hassan.imam@uni-oldenburg.de
