"""
Document & URL Ingestion Helper
Extracts clean plain text from public URLs (quotes, broker pages, website specs)
and uploaded documents to enrich call transcripts before AI inference.
"""
import urllib.request
import re
from typing import Optional
from bs4 import BeautifulSoup


def extract_text_from_url(url: str, max_chars: int = 4000) -> str:
    """
    Fetch web page content, strip HTML boilerplate, and return readable body text.
    """
    if not url or not url.strip():
        return ""
    
    clean_url = url.strip()
    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url

    try:
        req = urllib.request.Request(
            clean_url,
            headers={"User-Agent": "Mozilla/5.0 (nuDesk DeskMate Ops Studio Ingestion Bot)"}
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            html = response.read().decode("utf-8", errors="ignore")
            
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
    Extract text content from an uploaded text/markdown or plain text file.
    """
    if uploaded_file is None:
        return ""
    try:
        content_bytes = uploaded_file.getvalue()
        text = content_bytes.decode("utf-8", errors="ignore")
        return text[:max_chars]
    except Exception as e:
        return f"[File Ingestion Note: Unable to decode file: {str(e)}]"
