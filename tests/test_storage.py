from pathlib import Path

from awep.fetcher import fetch_once
from awep.models import FetchRequest
from awep.storage import EvidenceStore


def test_writes_receipt_snapshots_and_event(tmp_path: Path, httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://example.com",
        html="<title>T</title><p>" + "hello " * 80 + "</p>",
    )
    store = EvidenceStore(tmp_path / ".awep")
    receipt = store.write_fetch_result(
        fetch_once(FetchRequest(url="https://example.com", run_id="run-test"))
    )
    root = store.run_path("run-test")
    assert (root / "receipts" / f"{receipt.event_id}.json").exists()
    assert (root / "events.jsonl").exists()
    assert (root / receipt.extraction.markdown_path).exists()
    assert receipt.receipt_hash
