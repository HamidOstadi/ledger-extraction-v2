# Confidence-Aware Extraction of Historical Ledger Records

## A Multimodal Pipeline for Scanned Archival Documents

**Hamid Ostadi**
HaI Lab, Saïd Business School
Week 2 Project Report

---

## 1. Introduction

Historical financial ledgers constitute a rich but methodologically challenging source for economic and social research. While these documents often span centuries and contain highly structured financial information, they are typically preserved as scanned images, lack machine-readable text, and follow accounting conventions that differ substantially from modern standards. As a result, large-scale quantitative analysis of such archives has traditionally relied on labor-intensive manual transcription.

In the first week of this project, the focus was on developing an end-to-end pipeline for extracting structured transaction-level data from scanned ledger pages using multimodal large language models (LLMs). That work demonstrated that it is possible to recover semantically meaningful entries—such as descriptions, transaction types, and historical currency amounts—from image-only PDFs using a combination of OCR and schema-guided extraction. However, a key limitation of this initial pipeline was that correctness and reliability were assessed largely through manual inspection, with uncertainty remaining implicit rather than explicitly quantified.

The objective of the present work is to extend the previous pipeline by introducing a **confidence-aware extraction framework**. Instead of producing a single deterministic output per ledger entry, the system now attaches interpretable confidence scores at both **the field and row levels**. These scores quantify the model’s own certainty as well as the plausibility of extracted values under historically grounded accounting rules. By making uncertainty explicit and machine-readable, the pipeline is better suited for scalable archival analysis and selective human review.

---

## 2. Data and Challenges

The dataset consists of 33 scanned ledger volumes covering the period from the early eighteenth to the late nineteenth century. Each volume is stored as a PDF file named by year (e.g., `1704.pdf`) and contains multiple pages of handwritten or early printed accounting records. None of the PDFs include embedded text; all content is stored as rasterized images.

Several challenges arise from the nature of this material:

1. **Image-only sources**: Standard PDF text extraction tools fail because the documents contain no machine-readable text. Optical character recognition (OCR) is therefore a necessary first step.
2. **Historical currency systems**: Monetary values are expressed in pounds, shillings, and pence (£/s/d), often with fractional pence (e.g., 1/4, 1/2, 3/4). These units follow constraints that differ from modern decimal systems and must be preserved rather than normalized.
3. **Layout variability**: Ledger formats vary substantially across years and even within a single volume, including summary pages, sectional lists, and pages with totals interspersed among individual entries.
4. **No ground truth at scale**: While small subsets can be manually transcribed, a full gold-standard dataset is unavailable, making explicit uncertainty estimation particularly valuable.

---

## 3. Methodology

### 3.1 OCR via Multimodal Language Models

To address the lack of embedded text, each PDF page is first converted into a high-resolution image. These images are then passed to a vision-capable large language model, which is prompted to perform faithful line-by-line transcription of all visible text. The model is instructed explicitly not to summarize or interpret the content at this stage, but only to reproduce the textual structure of the page.

To ensure scalability and reproducibility, OCR outputs are cached to disk on a per-page basis. This design choice allows the pipeline to be restarted without reissuing OCR requests and separates the transcription stage cleanly from downstream semantic processing.

### 3.2 Unified Ledger Schema

All extracted transactions are mapped to a unified schema that is stable across documents and years. Each ledger row includes:

* Identifiers (`doc_id`, `page_id`, `row_id`)
* A textual description of the entry
* A transaction type (`Credit`, `Debit`, or `Unknown`)
* Monetary fields (`pounds`, `shillings`, `pence`, and optional fractional pence)

Crucially, historical currency units are preserved in their original form. No attempt is made to convert values into modern decimal representations at the extraction stage. This decision reflects the goal of maintaining historical fidelity and avoiding premature transformations that could obscure original accounting practices.

### 3.3 Confidence Scoring Framework

The central contribution of this week’s work is the introduction of a multi-layer confidence scoring framework. For each extracted ledger row, three complementary forms of confidence are computed:

1. **Model-level confidence**: The language model is prompted to report its confidence for each extracted field (e.g., description, transaction type, monetary values). These scores capture the model’s internal certainty given the OCR text and prompt constraints.
2. **Rule-based confidence**: Independently of the model’s self-assessment, extracted rows are evaluated against simple but historically grounded rules. Examples include valid ranges for shillings and pence, the presence of a non-empty description, and the plausibility of monetary combinations.
3. **Final row confidence**: A weighted aggregation of model-level and rule-based confidence produces a single interpretable score per row. This value is intended as a headline indicator for downstream filtering and review.

By decomposing uncertainty into these layers, the system avoids treating confidence as a black-box scalar and instead provides diagnostic insight into why a particular extraction should be trusted or questioned.

---

## 4. Full-Corpus Application

The confidence-aware extraction pipeline was applied to the full collection of scanned ledger volumes. In total, 33 yearly PDFs were processed, each containing multiple pages of image-only historical accounting records. The pipeline operated in batch mode, automatically iterating over all documents placed in the raw data directory and applying OCR, semantic classification, structured extraction, and confidence scoring to every page.

Across the corpus, each PDF was first decomposed into individual page images, which were then transcribed using a multimodal language model. To ensure computational efficiency and reproducibility, OCR outputs were cached at the page level. This design allows the extraction and confidence-scoring stages to be re-run without repeating the costly transcription step, making the pipeline robust to interruptions and iterative refinement.

The extracted outputs from all documents were consolidated into a single structured dataset. Two artifacts were produced:

- A row-level table containing all extracted ledger entries, including descriptions, transaction types, historical currency fields, and associated confidence scores.

- A page-level metadata table summarizing the semantic classification of each page and its inferred financial structure.

Both artifacts were exported into a single Excel workbook, with separate sheets for transaction-level data and page metadata. This consolidated output enables straightforward inspection, filtering, and downstream analysis using standard data analysis tools, while preserving traceability back to the original document year and page number.

## 5. Confidence Analysis

A central advantage of the proposed pipeline is that uncertainty is made explicit and quantifiable. Rather than relying on implicit trust in extracted values, each ledger entry is accompanied by interpretable confidence scores that reflect both model self-assessment and historically grounded validation rules.

Across the full corpus of **4,815 extracted rows**, row-level confidence scores exhibit a clear and interpretable distribution. The **average row confidence is 0.85**, with a **median value of 0.95**, indicating that a large share of extracted entries are assessed as highly reliable. At the same time, the presence of lower-confidence rows **(minimum observed value 0.27)** reflects genuine extraction difficulty arising from degraded scans, ambiguous handwriting, or irregular formatting.

The concentration of values near the upper end of the scale suggests that the pipeline performs consistently on well-structured ledger entries, while still providing meaningful differentiation in more challenging cases.

Qualitative inspection further supports this interpretation. High-confidence rows typically correspond to clearly legible entries with unambiguous monetary values, such as annual rents or standardized payments, where both OCR transcription and semantic parsing are straightforward. In contrast, lower-confidence rows tend to arise on pages with dense layouts, faded ink, partial totals, or non-standard annotations, where uncertainty is inherent even for human readers.

Crucially, the availability of explicit confidence scores enables selective human review. Rather than treating all extracted rows as equally reliable, researchers can prioritize inspection of low-confidence entries while accepting high-confidence rows with minimal intervention. This capability substantially reduces the manual burden associated with large archival datasets and aligns the extraction process with best practices in human–AI collaboration.

## 6. Discussion

The results of the full-corpus application highlight the value of making uncertainty explicit in large-scale archival extraction tasks. Rather than treating automated transcription and parsing as a binary success or failure, the proposed pipeline frames extraction quality as a graded outcome. This perspective is particularly well suited to historical data, where ambiguity, degradation, and non-standardized formats are inherent rather than exceptional.

A key advantage of the confidence-aware approach is its ability to separate different sources of uncertainty. Model-level confidence captures the language model’s own assessment given the OCR text and prompt constraints, while rule-based confidence reflects adherence to historically grounded accounting conventions. By keeping these components distinct before aggregation, the system avoids conflating model fluency with historical plausibility. This design choice improves interpretability and facilitates targeted debugging when extraction quality is low.

Compared to purely rule-based post-processing, which silently corrects or discards outputs, the present framework emphasizes transparency. Rules do not override the model’s output; instead, they contextualize it by signaling whether extracted values align with known constraints of the ledger system. This distinction is important for scholarly use, as it preserves the original model output while still enabling principled quality assessment.

The approach also complements related work on financial logic checks, such as consistency validation and total reconciliation. While such checks can further improve accuracy, embedding them within a confidence-scoring framework allows their influence to be quantified rather than applied deterministically. In this sense, confidence-aware scoring provides a unifying layer through which diverse validation strategies can be integrated.

More broadly, explicit confidence scoring supports a human–AI collaboration model that is well aligned with historical research practice. High-confidence entries can be incorporated directly into quantitative analyses, while low-confidence rows can be flagged for manual review or exclusion. This selective inspection paradigm offers substantial efficiency gains over exhaustive manual transcription while maintaining scholarly rigor.

## 7. Conclusion and Future Work

This project set out to extend an existing multimodal ledger extraction pipeline by making uncertainty explicit and operational. Building on prior work that demonstrated schema-guided extraction from scanned historical documents, the present contribution introduces a confidence-aware framework that quantifies extraction reliability at both the field and row levels. Applied to a corpus of 33 scanned ledger volumes, the system successfully extracted 4,815 transaction-level entries while providing interpretable confidence scores that reflect both model self-assessment and historically grounded validation rules.

The results demonstrate that confidence-aware extraction offers a practical and scalable alternative to purely manual transcription or opaque automated pipelines. By exposing uncertainty rather than masking it, the approach supports selective human review and enables researchers to balance scale with rigor. In this sense, the pipeline functions not as a replacement for historical expertise, but as an assistive research instrument that prioritizes transparency and interpretability.

Several directions for future work follow naturally from this framework. First, additional financial logic checks—such as reconciliation of page-level totals or cross-page consistency validation—could be incorporated as further contributors to the confidence score. Second, limited human-in-the-loop validation could be used to calibrate confidence thresholds and assess empirical accuracy on selected subsets of the data. Finally, the extracted and confidence-annotated dataset opens the door to substantive historical analysis, including longitudinal studies of rents, payments, and administrative practices across centuries.

Overall, this work demonstrates that large language models, when combined with explicit uncertainty modeling and domain-aware validation, can be deployed responsibly in archival research settings. The confidence-aware pipeline developed here provides a foundation for scalable, transparent, and methodologically sound analysis of historical financial records.