import os
import json
from typing import List

from openai import OpenAI  # <-- requires the openai package we installed

from .schema import PageMetadata, LedgerRow  # type: ignore[import]
from .scorer import (
    compute_rule_based_confidence,
    compute_row_confidence,
)  # type: ignore[import]
from .utils import load_env  # type: ignore[import]



def load_extraction_prompt_template() -> str:
    """
    Load the extraction prompt template from prompts/extraction_prompt.txt.
    Assumes this file is located in the 'prompts' directory at the project root.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, ".."))

    prompt_path = os.path.join(project_root, "prompts", "extraction_prompt.txt")

    with open(prompt_path, "r", encoding="utf-8") as f:
        template = f.read()

    return template


def build_extraction_prompt(
    page_meta: PageMetadata,
    page_text: str,
) -> str:
    """
    Fill the extraction prompt template with values from PageMetadata and the raw page text.
    Returns the final prompt string to be sent to the LLM.
    """
    template = load_extraction_prompt_template()

    prompt = (
        template
        .replace("{{DOC_ID}}", str(page_meta["doc_id"]))
        .replace("{{PAGE_ID}}", str(page_meta["page_id"]))
        .replace("{{PAGE_TYPE}}", page_meta["page_type"])
        .replace(
            "{{FINANCIAL_STRUCTURE_OVERVIEW}}",
            page_meta["financial_structure_overview"],
        )
        .replace("{{PAGE_TEXT}}", page_text)
    )

    return prompt

def extract_page_with_llm(
    page_meta: PageMetadata,
    page_text: str,
    model: str = "gpt-4o-mini",
) -> List[LedgerRow]:
    """
    LLM-backed extraction of ledger rows from a single page.
    """

    # Load environment and API key
    load_env()
    client = OpenAI()

    prompt = build_extraction_prompt(
        page_meta=page_meta,
        page_text=page_text,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise assistant that extracts structured ledger entries "
                    "and must respond with STRICT JSON only."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    content = response.choices[0].message.content
    if content is None:
        raise RuntimeError("LLM returned empty content for extraction.")

    data = json.loads(content)

    rows_data = data.get("rows", [])
    parsed_rows: List[LedgerRow] = []

    for i, r in enumerate(rows_data):

        doc_id = str(r.get("doc_id", page_meta["doc_id"]))
        page_id = int(r.get("page_id", page_meta["page_id"]))
        row_id = int(r.get("row_id", i))

        description = str(r.get("description", "") or "")
        tx_raw = r.get("transaction_type", "Unknown")
        tx_type = tx_raw if tx_raw in ("Debit", "Credit", "Unknown") else "Unknown"

        pounds = r.get("pounds")
        shillings = r.get("shillings")
        pence = r.get("pence")
        pence_fraction = r.get("pence_fraction")

        # Model confidences
        mc_desc = float(r.get("model_conf_description", 0.0))
        mc_tx = float(r.get("model_conf_transaction_type", 0.0))
        mc_pounds = float(r.get("model_conf_pounds", 0.0))
        mc_shillings = float(r.get("model_conf_shillings", 0.0))
        mc_pence = float(r.get("model_conf_pence", 0.0))
        mc_pf = float(r.get("model_conf_pence_fraction", 0.0))

        row: LedgerRow = {
            "doc_id": doc_id,
            "page_id": page_id,
            "row_id": row_id,
            "description": description,
            "transaction_type": tx_type,
            "pounds": pounds,
            "shillings": shillings,
            "pence": pence,
            "pence_fraction": pence_fraction,
            "model_conf_description": mc_desc,
            "model_conf_transaction_type": mc_tx,
            "model_conf_pounds": mc_pounds,
            "model_conf_shillings": mc_shillings,
            "model_conf_pence": mc_pence,
            "model_conf_pence_fraction": mc_pf,
            "rule_based_confidence": 0.0,
            "row_confidence": 0.0,
        }

        parsed_rows.append(row)

    return parsed_rows


def extract_page(
    page_meta: PageMetadata,
    page_text: str,
) -> List[LedgerRow]:
    """
    Public entry point for row extraction.

    Tries:
    1) LLM extraction
    2) Falls back to dummy extraction
    3) Applies rule-based + combined confidence to all rows
    """

    rows: List[LedgerRow] = []

    try:
        rows = extract_page_with_llm(
            page_meta=page_meta,
            page_text=page_text,
        )
    except Exception as e:
        print("[extract_page] LLM error, using fallback:", repr(e))

        # Dummy fallback row
        base_description = (
            "Dummy balance entry inferred from summary-like page text."
            if page_meta["page_type"] == "Full_Balance_Sheet"
            else "Dummy individual transaction inferred from list-like page text."
        )

        dummy_row: LedgerRow = {
            "doc_id": page_meta["doc_id"],
            "page_id": page_meta["page_id"],
            "row_id": 0,
            "description": base_description,
            "transaction_type": "Unknown",
            "pounds": None,
            "shillings": None,
            "pence": None,
            "pence_fraction": None,
            "model_conf_description": 0.3,
            "model_conf_transaction_type": 0.2,
            "model_conf_pounds": 0.0,
            "model_conf_shillings": 0.0,
            "model_conf_pence": 0.0,
            "model_conf_pence_fraction": 0.0,
            "rule_based_confidence": 0.0,
            "row_confidence": 0.0,
        }

        rows = [dummy_row]

    # Apply rule-based & combined confidences
    for row in rows:
        rb = compute_rule_based_confidence(row=row)
        combined = compute_row_confidence(row=row, rule_weight=0.4)
        row["rule_based_confidence"] = rb
        row["row_confidence"] = combined

    return rows
