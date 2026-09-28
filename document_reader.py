"""
Document & URL Ingestion Helper
Extracts clean plain text from public URLs (quotes, broker pages, website specs)
and uploaded documents to enrich call transcripts before AI inference.
"""
import io
import re
import shutil
import subprocess
import urllib.request
from typing import Optional
from bs4 import BeautifulSoup

try:
    import pypdf
except ImportError:
    pypdf = None


def extract_text_from_pdf_bytes(pdf_bytes: bytes, max_chars: int = 6000) -> str:
    """
    Extract readable text from raw PDF bytes using pypdf with pdftotext CLI fallback.
    """
    if not pdf_bytes:
        return ""

    # Attempt 1: pypdf library
    if pypdf is not None:
        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            pages_text = []
            for idx, page in enumerate(reader.pages):
                extracted = page.extract_text() or ""
                if extracted.strip():
                    pages_text.append(f"[Page {idx + 1}]\n{extracted.strip()}")
            full_text = "\n\n".join(pages_text).strip()
            if full_text:
                return full_text[:max_chars]
        except Exception:
            pass

    # Attempt 2: pdftotext CLI fallback (available on Linux / poppler-utils)
    if shutil.which("pdftotext"):
        try:
            proc = subprocess.run(
                ["pdftotext", "-", "-"],
                input=pdf_bytes,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            if proc.returncode == 0:
                txt = proc.stdout.decode("utf-8", errors="ignore").strip()
                if txt:
                    return txt[:max_chars]
        except Exception:
            pass

    return "[PDF Ingestion Note: Document is an encrypted or image-only scanned PDF. Text could not be extracted.]"


def extract_text_from_url(url: str, max_chars: int = 4000) -> str:
    """
    Fetch web page or document content, handle HTML or PDF, and return readable body text.
    """
    if not url or not url.strip():
        return ""
    
    clean_url = url.strip()
    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url

    try:
        req = urllib.request.Request(
            clean_url,
            headers={"User-Agent": "Mozilla/5.0 (nuDesk Ops Studio Ingestion Bot)"}
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            content_type = response.headers.get("Content-Type", "").lower()
            raw_bytes = response.read()

        # Check if response is PDF either by content type, header, or URL extension
        if "application/pdf" in content_type or raw_bytes.startswith(b"%PDF") or clean_url.lower().endswith(".pdf"):
            pdf_text = extract_text_from_pdf_bytes(raw_bytes, max_chars=max_chars)
            return pdf_text
            
        html = raw_bytes.decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove script, style, nav, and footer tags
        for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            element.decompose()
            
        text = soup.get_text(separator=" ")
        # Collapse extra whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_chars]
    except Exception as e:
        return f"[Document Ingestion Note: Unable to scrape URL {clean_url}: {str(e)}]"


def extract_text_from_file(uploaded_file, max_chars: int = 6000) -> str:
    """
    Extract text content from an uploaded text/markdown or PDF file.
    """
    if uploaded_file is None:
        return ""
    try:
        content_bytes = uploaded_file.getvalue()
        file_name = getattr(uploaded_file, "name", "").lower()

        # If file is PDF, use dedicated PDF parser
        if file_name.endswith(".pdf") or content_bytes.startswith(b"%PDF"):
            return extract_text_from_pdf_bytes(content_bytes, max_chars=max_chars)

        text = content_bytes.decode("utf-8", errors="ignore")
        return text[:max_chars]
    except Exception as e:
        return f"[File Ingestion Note: Unable to decode file: {str(e)}]"
