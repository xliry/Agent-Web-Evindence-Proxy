from pathlib import Path

from awep.fetcher import fetch_once
from awep.models import FetchRequest
from awep.report import build_and_write_report
from awep.storage import EvidenceStore


def test_report_writes_markdown_and_json(tmp_path: Path, httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://example.com",
        html=(
            "<title>Example Domain</title><p>"
            "Example Domain is used for illustrative examples. "
            + "x " * 250
            + "</p>"
        ),
    )
    store = EvidenceStore(tmp_path / ".awep")
    store.write_fetch_result(
        fetch_once(
            FetchRequest(
                url="https://example.com",
                run_id="run-test",
                claim="Example Domain is used for illustrative examples",
            )
        )
    )
    path = build_and_write_report("run-test", store)
    text = path.read_text(encoding="utf-8")
    assert "# Agent Web Evidence Report" in text
    assert "Receipt hash" in text
    assert (store.run_path("run-test") / "evidence.json").exists()


def test_report_preserves_unicode_without_mojibake(tmp_path: Path, httpx_mock) -> None:
    title = "Claude/Codex/OpenCode · GitHub"
    body = "freeze-then-capture — browser state. 保姆级AI Agent智能体系统教程. " + "text " * 120
    httpx_mock.add_response(
        url="https://example.com/unicode",
        html=f"<title>{title}</title><p>{body}</p>",
    )
    store = EvidenceStore(tmp_path / ".awep")
    store.write_fetch_result(
        fetch_once(
            FetchRequest(
                url="https://example.com/unicode",
                run_id="unicode-run",
                claim="freeze then capture browser state",
            )
        )
    )
    path = build_and_write_report("unicode-run", store)
    report = path.read_text(encoding="utf-8")
    evidence = (store.run_path("unicode-run") / "evidence.json").read_text(encoding="utf-8")
    assert "Claude/Codex/OpenCode · GitHub" in report
    assert "freeze-then-capture — browser state" in report
    assert "保姆级AI Agent智能体系统教程" in report
    assert "保姆级AI Agent智能体系统教程" in evidence
    for bad in ("Ã‚Â·", "Ã¢â‚¬â€", "Ã£â‚¬"):
        assert bad not in report
