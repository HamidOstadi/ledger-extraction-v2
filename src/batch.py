# src/batch.py

import os
import glob
from typing import List, Dict, Tuple

import pandas as pd

from .ocr import ocr_page_with_gpt  # type: ignore[import]
from .loader import export_pdf_pages_as_images  # type: ignore[import]
from .pipeline import process_document  # type: ignore[import]


def _project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def list_doc_ids_from_raw() -> List[str]:
    """
    Find all PDFs in data/raw and return doc_ids (filename without .pdf).
    Example: data/raw/1704.pdf -> "1704"
    """
    root = _project_root()
    raw_dir = os.path.join(root, "data", "raw")
    pdfs = sorted(glob.glob(os.path.join(raw_dir, "*.pdf")))
    doc_ids = [os.path.splitext(os.path.basename(p))[0] for p in pdfs]
    return doc_ids


def _ocr_cache_dir(doc_id: str) -> str:
    root = _project_root()
    d = os.path.join(root, "data", "interim", doc_id, "ocr_text")
    os.makedirs(d, exist_ok=True)
    return d


def ocr_pdf_to_pages_cached(
    doc_id: str,
    model: str = "gpt-4o-mini",
) -> Dict[int, str]:
    """
    OCR all pages of a PDF, but cache each page's transcription to:
        data/interim/{doc_id}/ocr_text/page_{page_id}.txt

    If the txt exists, reuse it (no API call).
    """
    page_images = export_pdf_pages_as_images(doc_id)
    cache_dir = _ocr_cache_dir(doc_id)

    pages_text: Dict[int, str] = {}

    for page_id, image_path in sorted(page_images.items()):
        cache_path = os.path.join(cache_dir, f"page_{page_id}.txt")

        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                pages_text[page_id] = f.read()
            continue

        print(f"[OCR] {doc_id} page {page_id} -> {image_path}")
        page_text = ocr_page_with_gpt(image_path, model=model)
        pages_text[page_id] = page_text

        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(page_text)

    return pages_text


def process_all_pdfs_to_excel(
    output_excel_name: str = "all_years_rows.xlsx",
    model_ocr: str = "gpt-4o-mini",
) -> str:
    """
    Batch process all PDFs in data/raw/*.pdf:
      PDF -> images -> OCR (cached) -> LLM classify/extract -> rows
    Then write a single Excel file with ALL rows.

    Returns:
      path to saved Excel file
    """
    doc_ids = list_doc_ids_from_raw()
    if not doc_ids:
        raise FileNotFoundError("No PDFs found in data/raw/*.pdf")

    all_rows: List[dict] = []
    all_pages_meta: List[dict] = []

    for doc_id in doc_ids:
        print(f"\n=== Processing {doc_id} ===")

        pages = ocr_pdf_to_pages_cached(doc_id, model=model_ocr)

        doc_meta, doc_rows = process_document(doc_id, pages)

        all_pages_meta.extend(doc_meta)
        all_rows.extend(doc_rows)

        print(f"Finished {doc_id}: pages={len(doc_meta)}, rows={len(doc_rows)}")

    df_rows = pd.DataFrame(all_rows)
    df_meta = pd.DataFrame(all_pages_meta)

    root = _project_root()
    out_dir = os.path.join(root, "data", "processed")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, output_excel_name)

    # Two sheets: one for rows, one for page metadata (super useful for QA)
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df_rows.to_excel(writer, sheet_name="rows", index=False)
        df_meta.to_excel(writer, sheet_name="page_metadata", index=False)

    return out_path
