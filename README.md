# Ledger Extraction v2  
### Confidence-Aware Multimodal Extraction of Historical Financial Ledgers

This repository contains a confidence-aware pipeline for extracting structured transaction-level data from **scanned historical ledger PDFs** using multimodal large language models (LLMs). The system performs OCR, schema-guided semantic extraction, and interpretable confidence scoring at scale, enabling transparent and selective human review of archival financial records.

The project was developed as part of a Week 2 research task at the **HaI Lab, Saïd Business School**, building on an earlier extraction-only prototype by explicitly modeling uncertainty.

---

## Project Overview

Historical ledgers are a valuable but challenging data source:
- They are typically preserved as **scanned images** with no embedded text.
- They follow **non-modern accounting conventions** (e.g. pounds–shillings–pence).
- Manual transcription does not scale to large archival collections.

This project addresses these challenges with an end-to-end pipeline that:

1. Converts scanned PDF pages into images  
2. Uses a vision-capable LLM to perform OCR (line-preserving transcription)  
3. Applies schema-guided semantic extraction to identify ledger entries  
4. Assigns **explicit confidence scores** at both field and row levels  
5. Outputs a consolidated, analysis-ready dataset for downstream research

---

## Key Features

- **Multimodal OCR**  
  Uses a vision-capable LLM to transcribe image-only ledger pages.

- **Unified Historical Schema**  
  Preserves original currency units (£ / s / d + fractional pence) without premature normalization.

- **Confidence-Aware Extraction**  
  Each extracted row includes:
  - model-reported confidence (per field)
  - rule-based confidence (historical plausibility checks)
  - a final aggregated row-level confidence score

- **Scalable Batch Processing**  
  Processes dozens of PDFs with page-level OCR caching for reproducibility.

- **Human–AI Collaboration**  
  Confidence scores enable selective human review rather than blind automation.

---

## Repository Structure



---

## Data Availability

⚠️ **Ledger PDFs and derived OCR outputs are not included in this repository** due to size and archival constraints.

To run the pipeline, users should place scanned ledger PDFs in:

`data/raw/`


Each PDF should be named by year, e.g.:

`1704.pdf` `1705.pdf`
...

---

## Running the Pipeline (High-Level)

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set your OpenAI API key:

```bash
export OPENAI_API_KEY=your_key_here
```

3. Run batch extraction from a notebook or script:

```python
from src.batch import process_all_pdfs_to_excel
process_all_pdfs_to_excel("all_years_rows.xlsx")
```

This produces a consolidated Excel file with:

a `rows` sheet (transaction-level data + confidence scores)

a `page_metadata` sheet (page classification summaries)

#### Confidence Scoring Philosophy ####

Confidence is treated as a first-class output, not an afterthought.

- Model confidence captures the LLM’s own uncertainty.

- Rule-based confidence reflects adherence to historical accounting constraints.

- Final row confidence enables filtering, auditing, and selective review.

This design supports responsible large-scale use of AI in archival research.

#### Status ####

✔️ Fully functional
✔️ Applied to 33 scanned ledger volumes
✔️ 4,815 transaction rows extracted with confidence scores

Future work includes totals reconciliation, cross-page consistency checks, and human-in-the-loop calibration.

**Author:**

Hamid Ostadi
HaI Lab, Saïd Business School