# src/loader.py

import os
from typing import Dict

import pdfplumber


def get_pdf_path(doc_id: str) -> str:
    """
    Build the path to a raw PDF file for a given document ID.

    Expected file format:
        data/raw/{doc_id}.pdf

    Where doc_id is typically a four-digit year such as "1704", "1712", etc.

    Example:
        doc_id = "1704"  --> data/raw/1704.pdf
    """

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, ".."))
    pdf_path = os.path.join(project_root, "data", "raw", f"{doc_id}.pdf")
    return pdf_path


def load_pdf_as_pages(doc_id: str) -> Dict[int, str]:
    """
    Load a year-based ledger PDF (e.g. 1704.pdf) from data/raw/

    Parameters
    ----------
    doc_id : str
        Typically a 4-digit year, e.g. "1704".

    Returns
    -------
    pages : dict[int, str]
        Mapping from page_id (1-based index) to extracted text.
    """

    pdf_path = get_pdf_path(doc_id)

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found at: {pdf_path}")

    pages: Dict[int, str] = {}

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages[i] = text

    return pages

def get_pdf_path(doc_id: str) -> str:
    """
    Build the path to a raw PDF file for a given document ID.

    Expected file format:
        data/raw/{doc_id}.pdf

    Where doc_id is typically a four-digit year such as "1704".
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, ".."))
    pdf_path = os.path.join(project_root, "data", "raw", f"{doc_id}.pdf")
    return pdf_path


def load_pdf_as_pages(doc_id: str) -> Dict[int, str]:
    """
    CURRENTLY UNUSED for scanned images, but kept for reference.

    For text-based PDFs, this would extract text with pdfplumber.
    For your ledgers (image-only), we'll replace this with OCR later.
    """
    pdf_path = get_pdf_path(doc_id)

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found at: {pdf_path}")

    pages: Dict[int, str] = {}
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages[i] = text

    return pages


def export_pdf_pages_as_images(doc_id: str, resolution: int = 300) -> Dict[int, str]:
    """
    Export each page of data/raw/{doc_id}.pdf as a PNG image.

    Images are saved under:
        data/interim/{doc_id}/page_{page_id}.png

    Returns:
        A dict mapping page_id (1-based) -> image_path.
    """
    pdf_path = get_pdf_path(doc_id)

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found at: {pdf_path}")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, ".."))
    out_dir = os.path.join(project_root, "data", "interim", doc_id)
    os.makedirs(out_dir, exist_ok=True)

    page_images: Dict[int, str] = {}

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            page_image = page.to_image(resolution=resolution)
            out_path = os.path.join(out_dir, f"page_{i}.png")
            page_image.save(out_path, format="PNG")
            page_images[i] = out_path

    return page_images