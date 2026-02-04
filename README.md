# Automating the Information Extraction

A research-oriented toolkit for (1) identifying relevant scientific papers and (2) extracting structured information from full texts or metadata. The repository is organized into two main modules:

- **Paper Finder**: utilities for paper discovery, filtering, and candidate set construction  
- **Info Extractor**: utilities for extracting structured study-level fields (e.g., sample size, demographics, setting, assessment timepoints), supporting reproducible downstream analysis

> **Goal:** Support transparent, reproducible information extraction workflows for evidence synthesis and meta-research.

---

## Repository structure

Automating-the-Information-Extraction/
├── Paper Finder/ # Paper search, retrieval helpers, filtering, candidate building
├── Info Extractor/ # Extraction logic, prompts/templates, parsers, output writers
├── README.md
└── .gitignore

> Note: Folder names currently contain spaces (e.g., `Paper Finder`). This is supported by Git, Python, and most tools. If you later prefer naming without spaces, rename carefully and update imports/paths.

---

## Requirements

- Python 3.9+ recommended
- (Optional) `pip`/`conda` environment for isolation

If you already have a `requirements.txt` (or `environment.yml`), use it. Otherwise, you can add one later once dependencies stabilize.

---

## Setup

### Option A: `venv` (pip)
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -U pip
# If you have requirements:
# pip install -r requirements.txt
Option B: Conda
conda create -n infoextract python=3.10
conda activate infoextract
# If you have requirements:
# pip install -r requirements.txt

Usage
1) Paper Finder

Typical workflow:

Define your query/search strategy

Collect candidate results (IDs/DOIs/URLs)

Store a reproducible candidate list (CSV/JSON)

Run scripts from inside Paper Finder/ (examples; adjust to your filenames):

cd "Paper Finder"
python <your_script>.py --help

2) Info Extractor

Typical workflow:

Provide paper PDFs or text exports

Run extraction to generate a structured output (CSV/TSV/JSON)

Validate extracted fields and keep an audit trail (evidence spans, notes)

Run scripts from inside Info Extractor/:

cd "Info Extractor"
python <your_script>.py --help

Data and reproducibility

Large datasets and PDFs should generally not be committed to GitHub.

Prefer storing inputs in a local data/ folder (ignored by git) and exporting clean, versioned outputs to outputs/ (also typically ignored unless you want to publish results).

If you intend to publish a small example dataset, consider:

data/sample/ (tiny, anonymized or public)

outputs/example/ (small demonstration outputs)

Contributing

Contributions are welcome via issues and pull requests. For reproducibility:

Describe data sources clearly

Pin versions when possible

Keep scripts deterministic and log key parameters

Citation

If you use this repository in academic work, please cite it as software:

Sana Hassan Imam. Automating the Information Extraction. GitHub repository.

(Add a DOI later via Zenodo if you want a formal software citation.)

License

See the LICENSE file in this repository.

Contact

Maintainer: Sana Hassan Imam
GitHub: sanahassanimam


---

## .gitignore (Python-focused)

```gitignore
# =========================
# Python / Bytecode
# =========================
__pycache__/
*.py[cod]
*$py.class

# =========================
# Virtual environments
# =========================
.venv/
venv/
ENV/
env/
.conda/
conda-env/
# (If you use conda, environments are usually outside the repo,
# but some people keep them here.)

# =========================
# Packaging / build
# =========================
build/
dist/
*.egg-info/
.eggs/
pip-wheel-metadata/

# =========================
# Test / coverage
# =========================
.pytest_cache/
.coverage
coverage.xml
htmlcov/
.tox/
.nox/

# =========================
# Jupyter / IPython
# =========================
.ipynb_checkpoints/
profile_default/
ipython_config.py

# =========================
# IDEs / editors
# =========================
.vscode/
.idea/
*.iml
*.swp
.DS_Store
Thumbs.db

# =========================
# Logs / temp files
# =========================
*.log
*.tmp
*.temp

# =========================
# Secrets (IMPORTANT)
# =========================
.env
.env.*
*.key
*.pem
*secret*
*apikey*
*api_key*

# =========================
# Data / outputs (recommended to keep out of git)
# Adjust these to your workflow
# =========================
data/
datasets/
outputs/
results/
cache/
tmp/

# =========================
# PDFs & large documents (optional)
# If your repo should include PDFs, REMOVE these lines.
# =========================
*.pdf

# =========================
# Model artifacts (optional)
# =========================
models/
checkpoints/
*.pt
*.pth
*.onnx
