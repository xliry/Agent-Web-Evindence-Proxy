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


def test_ok_source_with_low_lexical_overlap_is_missing_not_fetch_failure() -> None:
    claim = evaluate_claim_against_text(
        "Bilibili contains Chinese AI Agent tutorial content used as a market signal.",
        "保姆级AI Agent智能体系统教程：从基础概念到工作流实践，"
        "包含工具调用、规划、记忆和应用案例。",
        OK,
    )
    assert claim is not None
    assert claim.status == "missing"
    assert claim.score < 0.25


def test_blocked_quality_claim() -> None:
    claim = evaluate_claim_against_text("Anything", "", QualityEvidence(status="blocked"))
    assert claim is not None
    assert claim.status == "blocked"
