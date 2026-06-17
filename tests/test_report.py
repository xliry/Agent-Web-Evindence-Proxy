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
