# Automating-the-Information-Extraction

This repository contains **two independent but complementary tools** for academic workflows:

- **Paper Finder** — for *discovering and shortlisting* relevant research papers from multiple scholarly platforms.
- **Info Extractor** — for *extracting structured information* from a **specific paper (PDF)** based on a user-defined schema, using heuristics and optionally a local LLM (Ollama).

The tools are deliberately separated:
- **Paper Finder** answers *“Which papers should I look at?”*
- **Info Extractor** answers *“What structured information can I extract from this paper?”*

---

## **Repository Structure**

Automating-the-Information-Extraction/
├── paper-finder/
│ └── search.html
└── info-extractor/
├── backend/
│ └── server.py
└── frontend/
└── extractor_ui.html


---

## **1. Paper Finder**

### **Purpose**
Paper Finder is a browser-based tool for **retrieving and shortlisting academic papers** from multiple sources.  
It supports rapid exploration and export of candidate papers for later screening or analysis.

### **Supported Platforms**
- **OpenAlex**
- **PubMed**
- **arXiv**

### **Key Features**
- Keyword-based search
- Publication year range filtering
- Per-source result limits
- Enable/disable individual sources
- Optional **open-access-only** filtering for OpenAlex
- Manual paper selection
- Export selected papers to **CSV**
- Open available **PDF links** (OA PDFs when available)

### **How to Run**
Paper Finder is a **static HTML application**.

**Option A — Open directly**
- Double-click `paper-finder/search.html`

**Option B — Serve locally (recommended)**
```bash
cd paper-finder
python -m http.server 5174

**Open in browser:**

http://127.0.0.1:5174/search.html
