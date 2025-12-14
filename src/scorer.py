# src/scorer.py

from typing import Optional
from .schema import LedgerRow  # type: ignore[import]


def compute_rule_based_confidence(
    row: LedgerRow,
    typical_max_pounds: Optional[int] = None,
) -> float:
    """
    Compute a simple rule-based confidence score for a single LedgerRow.
    The score is between 0.0 and 1.0 and reflects how 'sane' the row looks
    based on basic structural and numeric checks.

    This is intentionally simple for now and can be extended later.
    """

    score = 1.0

    # 1) Description length check
    description = (row.get("description") or "").strip()
    if len(description) == 0:
        score -= 0.4  # no description is a big red flag
    elif len(description) < 3:
        score -= 0.2  # extremely short / suspect

    # 2) Numeric sanity checks
    pounds = row.get("pounds")
    shillings = row.get("shillings")
    pence = row.get("pence")

    # 2a) shillings should normally be 0–19
    if shillings is not None:
        if not (0 <= shillings <= 19):
            score -= 0.2

    # 2b) pence should normally be 0–11 (pre-decimal)
    if pence is not None:
        if not (0 <= pence <= 11):
            score -= 0.2

    # 2c) pounds range sanity if we have a typical max
    if typical_max_pounds is not None and pounds is not None:
        if pounds > typical_max_pounds * 3:  # arbitrarily allow up to 3x
            score -= 0.2

    # 3) Transaction type check
    tx_type = row.get("transaction_type")
    if tx_type not in ("Debit", "Credit", "Unknown"):
        # Should never happen, but just in case
        score -= 0.3

    # 4) If all monetary fields are None, it's suspicious as a transaction row
    if pounds is None and shillings is None and pence is None:
        score -= 0.3

    # Clamp to [0.0, 1.0]
    if score < 0.0:
        score = 0.0
    elif score > 1.0:
        score = 1.0

    return score


def compute_row_confidence(
    row: LedgerRow,
    rule_weight: float = 0.4,
    typical_max_pounds: Optional[int] = None,
) -> float:
    """
    Combine model-reported field confidences with the rule-based confidence
    into a single row_confidence score in [0.0, 1.0].

    - rule_weight: how much weight to give to rule-based confidence
      (0.0 = ignore rules, 1.0 = rules only).
    """

    # 1) Compute rule-based confidence
    rule_conf = compute_rule_based_confidence(
        row=row,
        typical_max_pounds=typical_max_pounds,
    )

    # 2) Compute average model confidence across the numeric + description fields
    model_confs = [
        row.get("model_conf_description", 0.0),
        row.get("model_conf_transaction_type", 0.0),
        row.get("model_conf_pounds", 0.0),
        row.get("model_conf_shillings", 0.0),
        row.get("model_conf_pence", 0.0),
        row.get("model_conf_pence_fraction", 0.0),
    ]

    if len(model_confs) > 0:
        model_conf_avg = sum(model_confs) / len(model_confs)
    else:
        model_conf_avg = 0.0

    # 3) Weighted combination
    rw = max(0.0, min(1.0, rule_weight))  # clamp rule_weight
    combined = rw * rule_conf + (1.0 - rw) * model_conf_avg

    # Clamp final combined score
    if combined < 0.0:
        combined = 0.0
    elif combined > 1.0:
        combined = 1.0

    return combined
