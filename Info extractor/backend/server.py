import re
import json
from typing import Any, Dict, Optional, List, Tuple

import fitz  # PyMuPDF
import httpx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from jsonschema import Draft202012Validator

app = FastAPI(title="Tiny Paper Extractor (Heuristics + Ollama LLM)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local use
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"ok": True, "hint": "Use POST /extract and POST /schema_from_prompt. See /docs"}


def pdf_bytes_to_text_pages(pdf_bytes: bytes, max_pages: int = 30) -> List[Dict[str, Any]]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    n = min(len(doc), max_pages)
    for i in range(n):
        page = doc[i]
        text = page.get_text("text")
        pages.append({"page": i + 1, "text": text})
    return pages


def find_evidence(text: str, patterns: List[Tuple[str, str]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for field, pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE | re.MULTILINE)
        if m:
            span = m.group(0)
            start = max(m.start() - 120, 0)
            end = min(m.end() + 120, len(text))
            out[field] = {
                "value": m.group(1).strip() if m.lastindex else span.strip(),
                "evidence": span.strip(),
                "context": text[start:end],
            }
    return out


def build_output_from_schema(schema: Dict[str, Any], extracted: Dict[str, Any]) -> Dict[str, Any]:
    """
    Top-level object schema -> ensure keys exist; fill from extracted, else null.
    """
    if schema.get("type") != "object":
        return extracted

    props = schema.get("properties", {}) or {}
    result: Dict[str, Any] = {}
    for key in props.keys():
        result[key] = extracted.get(key, None)
    return result


def validate_or_report(schema: Dict[str, Any], data: Dict[str, Any]) -> Optional[List[str]]:
    try:
        v = Draft202012Validator(schema)
        errors = sorted(v.iter_errors(data), key=lambda e: e.path)
        if errors:
            return [f"{list(e.path)}: {e.message}" for e in errors]
        return None
    except Exception as e:
        return [f"Schema validation failed to run: {e}"]


def _safe_first_n_pages_text(pages: List[Dict[str, Any]], n: int) -> str:
    n = max(1, min(int(n), len(pages) if pages else 1))
    return "\n\n".join([f"[PAGE {p['page']}]\n{p['text']}" for p in pages[:n]])


def _is_missing_value(v: Any) -> bool:
    return v is None or (isinstance(v, str) and v.strip().lower() in ("", "null"))


def guess_title_from_first_page(first_page_text: str) -> Optional[str]:
    lines = [ln.strip() for ln in first_page_text.splitlines() if ln.strip()]
    bad_prefixes = (
        "doi", "abstract", "keywords", "introduction", "open access",
        "received", "accepted", "copyright", "preprint", "arxiv"
    )
    cleaned = []
    for ln in lines[:100]:
        low = ln.lower()
        if low.startswith(bad_prefixes):
            continue
        if "@" in ln:
            continue
        if re.search(r"\b(university|department|institute|hospital|laboratory|faculty|school)\b", low):
            continue
        if 12 <= len(ln) <= 220:
            cleaned.append(ln)

    if not cleaned:
        return None

    title = " ".join(cleaned[:3])
    title = re.sub(r"\s+", " ", title).strip()
    return title if len(title) >= 12 else None


def _clean_field_token(token: str) -> Optional[str]:
    t = token.strip()
    if not t:
        return None
    is_array = False
    if t.endswith("[]"):
        is_array = True
        t = t[:-2].strip()

    t = re.sub(r"\s+", "_", t)
    t = re.sub(r"[^A-Za-z0-9_]", "_", t)
    t = re.sub(r"_+", "_", t).strip("_")
    t = t.lower()
    if not t:
        return None
    return f"{t}[]" if is_array else t


def _coerce_llm_output_to_object(schema: Dict[str, Any], llm_obj: Any) -> Dict[str, Any]:
    """
    If schema expects object but LLM returned list etc., coerce or raise.
    """
    if schema.get("type") != "object":
        if isinstance(llm_obj, dict):
            return llm_obj
        raise ValueError(f"Schema type is {schema.get('type')} but LLM returned {type(llm_obj)}")

    if isinstance(llm_obj, dict):
        return llm_obj

    if isinstance(llm_obj, list):
        # Try list of {field,value} pairs
        props = schema.get("properties", {}) or {}
        out: Dict[str, Any] = {}
        for item in llm_obj:
            if isinstance(item, dict):
                k = item.get("field") or item.get("key") or item.get("name")
                v = item.get("value")
                if isinstance(k, str) and k in props:
                    out[k] = v
        if out:
            return out

        # If list of strings and schema has a single array property, map it
        arr_props = []
        for k, subschema in (schema.get("properties", {}) or {}).items():
            if isinstance(subschema, dict):
                t = subschema.get("type")
                if t == "array" or (isinstance(t, list) and "array" in t):
                    arr_props.append(k)
        if len(arr_props) == 1 and all(isinstance(x, str) for x in llm_obj):
            return {arr_props[0]: llm_obj}

        raise ValueError("LLM returned a JSON list but schema expects an object.")
    raise ValueError(f"LLM returned {type(llm_obj)} but schema expects an object.")


async def call_ollama_json(model: str, prompt: str) -> Any:
    base = "http://127.0.0.1:11434"

    async with httpx.AsyncClient(timeout=180) as client:
        text = None

        # Try /api/generate
        try:
            r = await client.post(
                f"{base}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0},
                },
            )
            r.raise_for_status()
            data = r.json()
            text = (data.get("response") or "").strip()
        except Exception:
            pass

        # Fallback /api/chat
        if not text:
            r = await client.post(
                f"{base}/api/chat",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"temperature": 0},
                },
            )
            r.raise_for_status()
            data = r.json()
            text = (data.get("message", {}) or {}).get("content", "").strip()

    # Extract first JSON array or object from response
    s_obj, e_obj = text.find("{"), text.rfind("}")
    s_arr, e_arr = text.find("["), text.rfind("]")

    candidate = None
    if s_arr != -1 and e_arr != -1 and e_arr > s_arr:
        candidate = text[s_arr:e_arr + 1]
    elif s_obj != -1 and e_obj != -1 and e_obj > s_obj:
        candidate = text[s_obj:e_obj + 1]

    if not candidate:
        raise ValueError("Ollama did not return JSON. First 400 chars: " + text[:400])

    try:
        return json.loads(candidate)
    except Exception as e:
        raise ValueError(f"Could not parse JSON from Ollama: {e}. First 400 chars: {text[:400]}")


@app.post("/schema_from_prompt")
async def schema_from_prompt(
    user_request: str = Form(...),
    llm_model: str = Form(default="llama3:latest"),
):
    prompt = f"""
Convert the user's request into a CLEAN field list for information extraction from academic papers.

Output rules:
- Output ONLY a JSON array of strings. No extra text.
- Use snake_case field names.
- Use authors[] for multiple authors.
- Use arrays only when user clearly requests lists.
- Prefer stable, short keys (title, authors[], year, doi, sample_size, TR, TE, scanner, smoothing, etc.).
- Do NOT invent fields not implied by the request.

User request:
{user_request}
""".strip()

    try:
        obj = await call_ollama_json(llm_model, prompt)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"LLM field generation failed: {e}")

    if not isinstance(obj, list) or not all(isinstance(x, str) for x in obj):
        raise HTTPException(status_code=400, detail="LLM did not return a JSON array of strings.")

    cleaned: List[str] = []
    seen = set()
    for x in obj:
        c = _clean_field_token(x)
        if not c:
            continue
        if c in seen:
            continue
        seen.add(c)
        cleaned.append(c)

    # small guard rails
    if re.search(r"\bauthor", user_request, flags=re.IGNORECASE) and "authors[]" not in seen:
        cleaned.insert(0, "authors[]")
    if re.search(r"\btitle\b", user_request, flags=re.IGNORECASE) and "title" not in seen:
        cleaned.insert(0, "title")

    return {"fields": cleaned}


@app.post("/extract")
async def extract(
    pdf_url: Optional[str] = Form(default=None),
    pdf_file: Optional[UploadFile] = File(default=None),
    schema_json: str = Form(...),
    user_prompt: str = Form(default=""),
    max_pages: int = Form(default=30),
    llm_enabled: bool = Form(default=False),
    llm_model: str = Form(default="llama3:latest"),
    llm_pages: int = Form(default=1),
):
    # Parse schema
    try:
        schema = json.loads(schema_json)
        if not isinstance(schema, dict):
            raise ValueError("schema_json must be a JSON object.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid schema_json: {e}")

    # Get PDF bytes
    pdf_bytes: Optional[bytes] = None
    if pdf_file is not None:
        pdf_bytes = await pdf_file.read()
    elif pdf_url:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.get(pdf_url, follow_redirects=True)
                r.raise_for_status()
                pdf_bytes = r.content
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch PDF from url: {e}")
    else:
        raise HTTPException(status_code=400, detail="Provide either pdf_url or pdf_file.")

    pages = pdf_bytes_to_text_pages(pdf_bytes, max_pages=max_pages)
    full_text = "\n\n".join([f"[PAGE {p['page']}]\n{p['text']}" for p in pages])

    # ✅ Improved sample_size patterns (covers: n=114, N = 114, 114 participants, sample of 114, etc.)
    patterns = [
        ("sample_size", r"\b[nN]\s*=\s*(\d+)\b"),
        ("sample_size", r"\b(sample size|participants|subjects|sample of)\b[^0-9]{0,15}(\d{2,5})\b"),
        ("TR", r"\bTR\b[^0-9]{0,25}(\d+(?:\.\d+)?)\s*(s|sec|secs|seconds)\b"),
        ("TE", r"\bTE\b[^0-9]{0,25}(\d+(?:\.\d+)?)\s*(ms|msec|milliseconds)\b"),
        ("scanner", r"\b(1\.5\s*[- ]?tesla|3\s*[- ]?tesla|7\s*[- ]?tesla|1\.5\s*T|3\s*T|7\s*T)\b"),
        ("smoothing", r"\bFWHM\b[^0-9]{0,25}(\d+(?:\.\d+)?)\s*mm\b"),
    ]

    # Because sample_size appears twice, we want FIRST match to win.
    evidence = {}
    for field, pat in patterns:
        m = re.search(pat, full_text, flags=re.IGNORECASE | re.MULTILINE)
        if m and field not in evidence:
            span = m.group(0)
            start = max(m.start() - 120, 0)
            end = min(m.end() + 120, len(full_text))
            # handle the second sample_size pattern where number is group(2)
            if field == "sample_size" and m.lastindex and m.lastindex >= 2 and m.group(2).isdigit():
                value = m.group(2).strip()
            else:
                value = m.group(1).strip() if m.lastindex else span.strip()
            evidence[field] = {"value": value, "evidence": span.strip(), "context": full_text[start:end]}

    extracted_flat = {k: v.get("value") for k, v in evidence.items()}

    extracted_json_llm = None
    llm_error = None
    mode_used = "heuristics"

    if llm_enabled:
        try:
            llm_text = _safe_first_n_pages_text(pages, llm_pages)
            llm_prompt = f"""
You are an information extraction system.
Return ONLY valid JSON (no extra text, no markdown).
IMPORTANT: Return a SINGLE JSON OBJECT (top-level must be {{...}}, not a list).

Follow the JSON Schema exactly (keys and structure).
If a value is unknown or not stated, use null.

IMPORTANT for title:
- "title" is the paper's main title (main heading), usually top of page 1 above authors.
- If the title spans multiple lines, join them with spaces.
- Do NOT return journal name, running headers, or section headings as the title.

IMPORTANT for authors:
- "authors" is the list of author names (not affiliations).
- Split multiple authors into a JSON array of strings.

JSON Schema:
{schema_json}

User instructions (optional):
{user_prompt}

Paper text (may be truncated; includes page markers):
{llm_text}
""".strip()

            raw_llm = await call_ollama_json(llm_model, llm_prompt)
            extracted_json_llm = _coerce_llm_output_to_object(schema, raw_llm)
            mode_used = "llm"
        except Exception as e:
            llm_error = str(e)
            extracted_json_llm = None
            mode_used = "heuristics"

    # ✅ Final output logic (fixed order):
    # 1) If LLM exists -> shape it to schema keys FIRST
    # 2) Then merge heuristics into any missing/null fields (including sample_size)
    if extracted_json_llm is not None:
        extracted_json = build_output_from_schema(schema, extracted_json_llm)

        # Merge heuristics into missing values (keys definitely exist now)
        for k, v in extracted_flat.items():
            if v is None:
                continue
            if k in extracted_json and _is_missing_value(extracted_json.get(k)):
                extracted_json[k] = v

        # title fallback
        if _is_missing_value(extracted_json.get("title")):
            first_page_text = pages[0]["text"] if pages else ""
            t = guess_title_from_first_page(first_page_text)
            if t:
                extracted_json["title"] = t

    else:
        extracted_json = build_output_from_schema(schema, extracted_flat)

    validation_errors = validate_or_report(schema, extracted_json)

    return {
        "extracted_json": extracted_json,
        "evidence": evidence,
        "validation_errors": validation_errors,
        "text_pages": pages,
        "notes": {
            "prompt_received": user_prompt[:500],
            "max_pages": max_pages,
            "heuristic_fields_found": list(evidence.keys()),
            "llm_enabled": llm_enabled,
            "llm_model": llm_model,
            "llm_pages_used": int(llm_pages),
            "llm_error": llm_error,
            "mode_used": mode_used,
            "merge_policy": "LLM first; then fill missing/nulls from heuristics (evidence-based)",
        },
    }
