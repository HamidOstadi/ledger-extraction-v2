# src/classifier.py

import os
import json

from typing import Any

from openai import OpenAI  # make sure 'openai' is installed
from .schema import PageMetadata, PageType  # type: ignore[import]
from .utils import load_env  # type: ignore[import]


def load_classifier_prompt_template() -> str:
    """
    Load the classifier prompt template from prompts/classifier_prompt.txt.
    Assumes this file is located in the 'prompts' directory at the project root.
    """
    # Find project root as the parent directory of this file's directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, ".."))

    prompt_path = os.path.join(project_root, "prompts", "classifier_prompt.txt")

    with open(prompt_path, "r", encoding="utf-8") as f:
        template = f.read()

    return template


def build_classifier_prompt(doc_id: str, page_id: int, page_text: str) -> str:
    """
    Fill the classifier prompt template with the given doc_id, page_id, and page_text.
    Returns the final prompt string to be sent to the LLM.
    """
    template = load_classifier_prompt_template()

    prompt = (
        template
        .replace("{{DOC_ID}}", str(doc_id))
        .replace("{{PAGE_ID}}", str(page_id))
        .replace("{{PAGE_TEXT}}", page_text)
    )

    return prompt

def classify_page_with_llm(
    doc_id: str,
    page_id: int,
    page_text: str,
    model: str = "gpt-4o-mini",
) -> PageMetadata:
    """
    LLM-backed page classification.

    Steps:
    - Build the classifier prompt.
    - Call the OpenAI Chat Completions API in JSON mode.
    - Parse the JSON into a PageMetadata object.
    """

    # Ensure environment variables (including OPENAI_API_KEY) are loaded
    load_env()

    client = OpenAI()

    prompt = build_classifier_prompt(
        doc_id=doc_id,
        page_id=page_id,
        page_text=page_text,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise assistant that classifies historical ledger pages "
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
        raise RuntimeError("LLM returned empty content for page classification.")

    data = json.loads(content)

    # Basic validation / defaults
    page_type_raw = data.get("page_type", "Unknown")
    if page_type_raw not in ("Full_Balance_Sheet", "Sectional_List", "Unknown"):
        page_type: PageType = "Unknown"
    else:
        page_type = page_type_raw  # type: ignore[assignment]

    financial_structure_overview = data.get(
        "financial_structure_overview",
        "",
    )

    meta: PageMetadata = {
        "doc_id": str(data.get("doc_id", doc_id)),
        "page_id": int(data.get("page_id", page_id)),
        "page_type": page_type,
        "financial_structure_overview": str(financial_structure_overview),
    }

    return meta


from typing import Any
from .schema import PageMetadata, PageType  # type: ignore[import]


# ... existing functions:
# load_classifier_prompt_template()
# build_classifier_prompt()


def classify_page(
    doc_id: str,
    page_id: int,
    page_text: str,
) -> PageMetadata:
    """
    Public entry point for page classification.

    Tries:
    1) LLM-based classification via classify_page_with_llm()
    2) Falls back to simple heuristic if anything fails (e.g., no API key, network issues)
    """

    try:
        meta = classify_page_with_llm(
            doc_id=doc_id,
            page_id=page_id,
            page_text=page_text,
        )
        return meta
    except Exception as e:
        # Fallback: simple heuristic based on keywords
        normalized_text = page_text.lower()

        if "total" in normalized_text or "balance" in normalized_text:
            page_type: PageType = "Full_Balance_Sheet"
            overview = (
                "Fallback: classified as balance/summary page based on presence "
                "of 'total' or 'balance'."
            )
        else:
            page_type = "Sectional_List"
            overview = (
                "Fallback: classified as list page using simple keyword heuristic."
            )

        meta: PageMetadata = {
            "doc_id": doc_id,
            "page_id": page_id,
            "page_type": page_type,
            "financial_structure_overview": overview,
        }

        return meta

