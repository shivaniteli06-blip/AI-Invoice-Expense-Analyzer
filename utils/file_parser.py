"""
File parser for invoices and receipts (text-based PDF and plain text).
No external OCR services — uses PyMuPDF for PDF text extraction.
"""
import io
import re
from typing import Optional


def extract_text_from_pdf(file_bytes: bytes) -> tuple[str, Optional[str]]:
    """
    Extract raw text from a PDF file.
    Returns (text, error_message). error_message is None on success.
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages_text = []
        for page in doc:
            pages_text.append(page.get_text())
        text = "\n".join(pages_text).strip()
        if not text:
            return "", "PDF appears to contain no extractable text (may be image-based). Please copy-paste the text manually."
        return text, None
    except ImportError:
        return "", "PyMuPDF is not installed. Install it with: pip install PyMuPDF"
    except Exception as e:
        return "", f"Could not read PDF: {e}"


def extract_text_from_txt(file_bytes: bytes) -> tuple[str, Optional[str]]:
    """Decode a plain text file. Returns (text, error)."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return file_bytes.decode(encoding).strip(), None
        except UnicodeDecodeError:
            continue
    return "", "Could not decode text file — unsupported encoding."


def parse_uploaded_file(
    filename: str, file_bytes: bytes
) -> tuple[str, Optional[str]]:
    """
    Route a file to the appropriate parser based on extension.
    Returns (raw_text, error_message).
    """
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif lower.endswith((".txt", ".text")):
        return extract_text_from_txt(file_bytes)
    else:
        return "", f"Unsupported file type: '{filename}'. Please upload a PDF or TXT file."
