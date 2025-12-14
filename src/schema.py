from typing import TypedDict, Literal, Optional

# -------------------------------
# Transaction-level definitions
# -------------------------------

TransactionType = Literal["Credit", "Debit", "Unknown"]

PenceFraction = Optional[Literal["q", "d", "1/4", "1/2", "3/4"]]


class LedgerRow(TypedDict):
    """
    A single extracted financial entry from a ledger, after semantic parsing
    and alignment. This schema remains consistent for all documents, including
    support for fractional penny values found in historical accounting systems.
    """

    # Identifiers
    doc_id: str
    page_id: int
    row_id: int

    # Core extracted content
    description: str
    transaction_type: TransactionType

    pounds: Optional[int]
    shillings: Optional[int]
    pence: Optional[int]
    pence_fraction: PenceFraction  # NEW fractional penny field

    # Model-reported confidences (0.0–1.0)
    model_conf_description: float
    model_conf_transaction_type: float
    model_conf_pounds: float
    model_conf_shillings: float
    model_conf_pence: float
    model_conf_pence_fraction: float

    # Rule-based + final combined confidence
    rule_based_confidence: float
    row_confidence: float


# -------------------------------
# Page-level definitions
# -------------------------------

PageType = Literal["Full_Balance_Sheet", "Sectional_List", "Unknown"]


class PageMetadata(TypedDict):
    """
    Metadata about a single page in a ledger document, produced by the
    semantic classifier before detailed row-level extraction.
    """

    doc_id: str
    page_id: int

    page_type: PageType
    financial_structure_overview: str
