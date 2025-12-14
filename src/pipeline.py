# src/pipeline.py

from typing import List, Tuple

from .schema import PageMetadata, LedgerRow  # type: ignore[import]
from .classifier import classify_page       # type: ignore[import]
from .extractor import extract_page         # type: ignore[import]


def process_single_page(
    doc_id: str,
    page_id: int,
    page_text: str,
) -> Tuple[PageMetadata, List[LedgerRow]]:
    """
    Minimal end-to-end processing for a single page.

    Steps:
    1. Classify the page to get PageMetadata (including page_type).
    2. Extract ledger rows from the page using the extraction module.

    For now, both classification and extraction are using heuristic/dummy logic.
    Later, they will be upgraded to call the LLM API and parse real outputs.
    """

    # Step 1: classify the page
    page_meta = classify_page(
        doc_id=doc_id,
        page_id=page_id,
        page_text=page_text,
    )

    # Step 2: extract rows using the page metadata
    rows = extract_page(
        page_meta=page_meta,
        page_text=page_text,
    )

    return page_meta, rows

def process_document(
    doc_id: str,
    pages: dict[int, str],
) -> Tuple[List[PageMetadata], List[LedgerRow]]:
    """
    Process a full document consisting of multiple pages.

    Parameters
    ----------
    doc_id : str
        Identifier for the ledger document (e.g. filename without extension).
    pages : dict[int, str]
        Mapping from page_id (1-based index, or any consistent integer) to
        the raw text content of that page.

    Returns
    -------
    all_page_meta : List[PageMetadata]
        One PageMetadata entry per page.
    all_rows : List[LedgerRow]
        All extracted ledger rows from all pages, with page_id filled in.
    """

    all_page_meta: List[PageMetadata] = []
    all_rows: List[LedgerRow] = []

    # Sort pages by page_id so processing is deterministic
    for page_id in sorted(pages.keys()):
        page_text = pages[page_id]

        page_meta, rows = process_single_page(
            doc_id=doc_id,
            page_id=page_id,
            page_text=page_text,
        )

        all_page_meta.append(page_meta)
        all_rows.extend(rows)

    return all_page_meta, all_rows
