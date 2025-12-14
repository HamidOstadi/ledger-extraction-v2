# src/ocr.py

import base64
import os

from openai import OpenAI  # requires 'openai' package installed
from .utils import load_env  # type: ignore[import]


def ocr_page_with_gpt(
    image_path: str,
    model: str = "gpt-4o-mini",
) -> str:
    """
    Use an OpenAI vision-capable model to perform OCR on a single ledger page image.

    Parameters
    ----------
    image_path : str
        Path to a PNG image of a single page (e.g. data/interim/1704/page_1.png).
    model : str
        A vision-capable chat model, e.g. "gpt-4o-mini".

    Returns
    -------
    page_text : str
        A plain-text transcription of the ledger page, line by line.
    """

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at: {image_path}")

    # Ensure environment variables (OPENAI_API_KEY) are loaded
    load_env()

    client = OpenAI()

    # Read image as base64
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    # Build the multimodal message: image + instructions
    messages = [
        {
            "role": "system",
            "content": (
                "You are a careful OCR assistant. You read historical ledger pages "
                "and transcribe the text faithfully, line by line, without adding "
                "extra interpretation."
            ),
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{b64_image}"
                    },
                },
                {
                    "type": "text",
                    "text": (
                        "Please transcribe all visible text from this ledger page.\n"
                        "- Preserve the line order from top to bottom.\n"
                        "- Separate lines with newline characters.\n"
                        "- Include column headers, names, places, and amounts.\n"
                        "- Do NOT summarise or interpret; just transcribe."
                    ),
                },
            ],
        },
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
    )

    content = response.choices[0].message.content
    if content is None:
        raise RuntimeError("OCR model returned empty content.")

    # The model response is plain text transcription
    page_text: str = content.strip()
    return page_text

from typing import Dict
from .loader import export_pdf_pages_as_images  # type: ignore[import]


def ocr_pdf_to_pages(
    doc_id: str,
    model: str = "gpt-4o-mini",
) -> Dict[int, str]:
    """
    Run OCR with GPT on all pages of data/raw/{doc_id}.pdf.

    Steps:
    - Export each page as PNG: data/interim/{doc_id}/page_{i}.png
    - Run ocr_page_with_gpt on each image
    - Return a dict mapping page_id -> transcribed text

    This output is directly usable as the `pages` argument to process_document().
    """

    # 1) Export pages as images
    page_images = export_pdf_pages_as_images(doc_id)

    pages_text: Dict[int, str] = {}

    # 2) OCR each page image
    for page_id, image_path in sorted(page_images.items()):
        print(f"[OCR] {doc_id} page {page_id} -> {image_path}")
        page_text = ocr_page_with_gpt(image_path, model=model)
        pages_text[page_id] = page_text

    return pages_text
