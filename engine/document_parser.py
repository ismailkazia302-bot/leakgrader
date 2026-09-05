"""
OmniBrain AI - Universal Multi-Format Document Parser
Supports PDF, TXT, Markdown, CSV, JSON, and Web URLs.
Performs semantic chunking with overlap & metadata tagging.
"""

import os
import re
import json
import csv
import io
import urllib.request
import urllib.error
import html

def extract_text_from_pdf(pdf_bytes: bytes) -> list[dict]:
    """
    Extracts text from PDF bytes page by page.
    Uses pypdf if available, or lightweight pure-Python PDF stream decoder.
    """
    pages = []
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append({"page": page_num, "text": text.strip()})
        if pages:
            return pages
    except Exception:
        pass

    # Lightweight fallback PDF text extractor
    try:
        raw = pdf_bytes.decode('latin-1', errors='ignore')
        text_blocks = []
        for match in re.finditer(r'stream[\r\n]+(.*?)[\r\n]+endstream', raw, re.DOTALL):
            stream_content = match.group(1)
            tjs = re.findall(r'\((.*?)\)\s*Tj', stream_content)
            if tjs:
                clean_line = " ".join(tjs)
                if len(clean_line.strip()) > 10:
                    text_blocks.append(clean_line)
        
        full_text = "\n".join(text_blocks)
        if full_text.strip():
            pages.append({"page": 1, "text": full_text.strip()})
        else:
            printable = "".join([c if ord(c) < 128 and (c.isalnum() or c in ' \n.,;:-_()[]/\"\'') else ' ' for c in raw])
            words = [w for w in printable.split() if len(w) > 2]
            if words:
                pages.append({"page": 1, "text": " ".join(words[:2000])})
    except Exception as e:
        pages.append({"page": 1, "text": f"[Error reading PDF: {e}]"})
    
    return pages if pages else [{"page": 1, "text": "Empty document."}]

def extract_text_from_url(url: str) -> str:
    """Fetches webpage content and cleans HTML tags."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OmniBrainAI/1.0"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw_html = resp.read().decode('utf-8', errors='ignore')
    
    cleaned = re.sub(r'<(script|style|nav|header|footer)[^>]*>.*?</\1>', '', raw_html, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'<(p|br|div|h[1-6]|li)[^>]*>', '\n', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<[^>]+>', ' ', cleaned)
    cleaned = html.unescape(cleaned)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
    return cleaned.strip()

def chunk_text(text: str, doc_name: str, page_num: int = 1, chunk_size: int = 700, chunk_overlap: int = 120) -> list[dict]:
    """
    Semantically chunks text by paragraphs/sentences with overlap.
    Returns list of chunk objects with rich metadata.
    """
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        para_len = len(para)
        if current_length + para_len > chunk_size and current_chunk:
            combined_text = " ".join(current_chunk)
            chunks.append({
                "doc_name": doc_name,
                "page": page_num,
                "content": combined_text,
                "length": len(combined_text)
            })
            overlap_text = current_chunk[-1] if len(current_chunk[-1]) < chunk_overlap else current_chunk[-1][-chunk_overlap:]
            current_chunk = [overlap_text, para]
            current_length = len(overlap_text) + para_len
        else:
            current_chunk.append(para)
            current_length += para_len

    if current_chunk:
        combined_text = " ".join(current_chunk)
        chunks.append({
            "doc_name": doc_name,
            "page": page_num,
            "content": combined_text,
            "length": len(combined_text)
        })

    return chunks

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown", ".csv", ".json", ".docx"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

def parse_file(file_name: str, file_bytes: bytes) -> list[dict]:
    """
    Main entrypoint: parses file content based on extension and returns indexed chunks.
    Validates supported file formats and maximum file size (10MB).
    """
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File size exceeds 10MB limit ({len(file_bytes)} bytes).")

    ext = os.path.splitext(file_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file format '{ext}'. Allowed formats: PDF, TXT, MD, CSV, JSON.")

    all_chunks = []

    if ext == ".pdf":
        pages = extract_text_from_pdf(file_bytes)
        for page in pages:
            chunks = chunk_text(page["text"], doc_name=file_name, page_num=page["page"])
            all_chunks.extend(chunks)

    elif ext in [".txt", ".md", ".markdown"]:
        text = file_bytes.decode('utf-8', errors='ignore')
        all_chunks.extend(chunk_text(text, doc_name=file_name, page_num=1))

    elif ext == ".csv":
        text = file_bytes.decode('utf-8', errors='ignore')
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        if rows:
            header = rows[0]
            row_texts = []
            for i, row in enumerate(rows[1:], start=1):
                row_str = " | ".join([f"{header[j] if j < len(header) else f'Col{j}'}: {val}" for j, val in enumerate(row)])
                row_texts.append(f"Row {i}: {row_str}")
            full_csv_text = "\n".join(row_texts)
            all_chunks.extend(chunk_text(full_csv_text, doc_name=file_name, page_num=1))

    elif ext == ".json":
        text = file_bytes.decode('utf-8', errors='ignore')
        try:
            data = json.loads(text)
            formatted_json = json.dumps(data, indent=2)
            all_chunks.extend(chunk_text(formatted_json, doc_name=file_name, page_num=1))
        except Exception:
            all_chunks.extend(chunk_text(text, doc_name=file_name, page_num=1))

    else:
        text = file_bytes.decode('utf-8', errors='ignore')
        all_chunks.extend(chunk_text(text, doc_name=file_name, page_num=1))

    for idx, c in enumerate(all_chunks, start=1):
        c["chunk_id"] = f"{file_name}#c{idx}"

    return all_chunks
