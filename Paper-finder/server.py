from flask import Flask, request, jsonify, send_file, send_from_directory
import io
import csv
import zipfile
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB

HEADERS = {"User-Agent": "PaperFinder/1.0 (local proxy)"}
TIMEOUT = 20


def normalize_title(t: str) -> str:
    return " ".join((t or "").split()).strip()


def safe_filename(s: str) -> str:
    s = (s or "file").strip()
    for ch in '\\/:*?"<>|':
        s = s.replace(ch, "_")
    s = " ".join(s.split())
    return (s[:140] if len(s) > 140 else s) or "file"


def parse_int(value, default: int) -> int:
    try:
        n = int(value)
        return n
    except Exception:
        return default


@app.get("/")
@app.get("/search.html")
def serve_html():
    return send_from_directory(".", "search.html")


@app.get("/api/pubmed")
def api_pubmed():
    q = request.args.get("q", "").strip()
    y1 = request.args.get("y1", "").strip()
    y2 = request.args.get("y2", "").strip()
    maxn = parse_int(request.args.get("max", "25"), 25)

    # Guard: enforce sensible bounds
    if maxn <= 0:
        maxn = 25
    maxn = min(maxn, 500)  # keep it fast/reliable

    if not q:
        return jsonify([])

    term = q
    if y1 or y2:
        term = f"({term}) AND ({y1 or 1800}:{y2 or 2100}[pdat])"

    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    # Search IDs
    esearch = (
        f"{base}/esearch.fcgi?db=pubmed&retmode=json"
        f"&retmax={maxn}&term={quote_plus(term)}"
    )
    sj = requests.get(esearch, headers=HEADERS, timeout=TIMEOUT).json()
    ids = sj.get("esearchresult", {}).get("idlist", [])

    if not ids:
        return jsonify([])

    # Summaries
    esummary = f"{base}/esummary.fcgi?db=pubmed&retmode=json&id={','.join(ids)}"
    sumj = requests.get(esummary, headers=HEADERS, timeout=TIMEOUT).json()
    result = sumj.get("result", {})

    out = []
    for pid in ids:
        it = result.get(pid)
        if not it:
            continue

        pubdate = (it.get("pubdate", "") or "")
        year = int(pubdate[:4]) if len(pubdate) >= 4 and pubdate[:4].isdigit() else None

        out.append({
            "id": f"PMID:{pid}",
            "title": normalize_title(it.get("title", "")),
            "authors": [a.get("name") for a in it.get("authors", []) if a.get("name")],
            "year": year,
            "venue": it.get("fulljournalname"),
            "source": "PubMed",
            "oa": None,
            "pdf_url": None,  # not resolved in this fast version
            "landing_url": f"https://pubmed.ncbi.nlm.nih.gov/{pid}/",
            "doi": None
        })

    return jsonify(out)


@app.get("/api/arxiv")
def api_arxiv():
    q = request.args.get("q", "").strip()
    y1 = request.args.get("y1", "").strip()
    y2 = request.args.get("y2", "").strip()
    maxn = parse_int(request.args.get("max", "25"), 25)

    # IMPORTANT: arXiv does NOT accept max_results=0
    if maxn <= 0:
        maxn = 25
    maxn = min(maxn, 500)  # keep it fast/reliable

    if not q:
        return jsonify([])

    url = (
        f"https://export.arxiv.org/api/query?"
        f"search_query=all:{quote_plus(q)}&start=0&max_results={maxn}"
    )

    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)

    # Don't crash Flask on arXiv transient errors; return 502 with message
    if not r.ok:
        return jsonify({
            "error": "arXiv request failed",
            "status_code": r.status_code,
            "details": r.text[:300]
        }), 502

    root = ET.fromstring(r.text)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entries = root.findall("a:entry", ns)

    out = []
    for e in entries:
        title = normalize_title(e.findtext("a:title", default="", namespaces=ns) or "")
        published = e.findtext("a:published", default="", namespaces=ns) or ""
        year = int(published[:4]) if len(published) >= 4 and published[:4].isdigit() else None

        if y1 and year and year < int(y1):
            continue
        if y2 and year and year > int(y2):
            continue

        authors = []
        for a in e.findall("a:author", ns):
            name = a.findtext("a:name", default="", namespaces=ns)
            if name:
                authors.append(name)

        abs_url = e.findtext("a:id", default="", namespaces=ns) or ""
        pdf_url = abs_url.replace("/abs/", "/pdf/") + ".pdf" if "/abs/" in abs_url else None

        out.append({
            "id": f"arXiv:{abs_url}",
            "title": title,
            "authors": authors,
            "year": year,
            "venue": "arXiv",
            "source": "arXiv",
            "oa": True,
            "pdf_url": pdf_url,
            "landing_url": abs_url,
            "doi": None
        })

    return jsonify(out)


@app.post("/api/zip")
def api_zip():
    papers = request.get_json(force=True, silent=True) or []
    if not isinstance(papers, list):
        return jsonify({"error": "Invalid payload: expected a JSON list"}), 400

    mem = io.BytesIO()
    z = zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED)

    # CSV
    headers = ["title", "authors", "year", "venue", "doi", "source", "oa", "pdf_url", "landing_url"]
    csv_buf = io.StringIO()
    w = csv.writer(csv_buf)
    w.writerow(headers)

    for p in papers:
        if not isinstance(p, dict):
            continue
        w.writerow([
            p.get("title", ""),
            "; ".join(p.get("authors") or []),
            p.get("year") or "",
            p.get("venue") or "",
            p.get("doi") or "",
            p.get("source") or "",
            "true" if p.get("oa") is True else "",
            p.get("pdf_url") or "",
            p.get("landing_url") or ""
        ])

    z.writestr("selected_papers.csv", csv_buf.getvalue())

    # links.txt
    lines = []
    for i, p in enumerate(papers, start=1):
        if not isinstance(p, dict):
            continue
        lines.append(f"#{i} {p.get('title','')}")
        lines.append(f"Source: {p.get('source','')}")
        lines.append(f"Year: {p.get('year') or '—'}")
        lines.append(f"Venue: {p.get('venue') or '—'}")
        lines.append(f"Landing: {p.get('landing_url','')}")
        lines.append(f"PDF: {p.get('pdf_url','')}")
        lines.append("")
    z.writestr("links.txt", "\n".join(lines))

    # PDFs (only where pdf_url exists: mainly arXiv)
    pdf_ok = 0
    for p in papers:
        if not isinstance(p, dict):
            continue
        pdf = p.get("pdf_url")
        if not pdf:
            continue
        try:
            rr = requests.get(pdf, headers=HEADERS, timeout=TIMEOUT)
            if rr.ok and (("pdf" in (rr.headers.get("content-type", "") or "").lower()) or rr.content.startswith(b"%PDF")):
                name = safe_filename(f"{p.get('source','src')}_{p.get('year','NA')}_{p.get('title','paper')}") + ".pdf"
                z.writestr(f"pdfs/{name}", rr.content)
                pdf_ok += 1
        except Exception:
            pass

    z.writestr("zip_log.txt", f"PDFs added: {pdf_ok}\n")

    z.close()
    mem.seek(0)

    return send_file(mem, mimetype="application/zip", as_attachment=True, download_name="selected_papers.zip")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5174, debug=False, threaded=True)
