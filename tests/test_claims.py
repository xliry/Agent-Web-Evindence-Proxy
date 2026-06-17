from awep.claims import evaluate_claim_against_text
from awep.models import QualityEvidence

OK = QualityEvidence(status="ok")


def test_supported_claim() -> None:
    claim = evaluate_claim_against_text(
        "Example Domain is used for illustrative examples",
        "Example Domain is used for illustrative examples in documents and demonstrations.",
        OK,
    )
    assert claim is not None
    assert claim.status == "supported"
    assert claim.snippet


def test_weak_claim() -> None:
    claim = evaluate_claim_against_text(
        "Example Domain released a private mobile API",
        "Example Domain is used for illustrative examples in documents.",
        OK,
    )
    assert claim is not None
    assert claim.status == "weak"


def test_missing_claim() -> None:
    claim = evaluate_claim_against_text("Revenue doubled in 2026", "A page about gardens.", OK)
    assert claim is not None
    assert claim.status == "missing"


def test_blocked_quality_claim() -> None:
    claim = evaluate_claim_against_text("Anything", "", QualityEvidence(status="blocked"))
    assert claim is not None
    assert claim.status == "blocked"
