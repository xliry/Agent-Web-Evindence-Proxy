import json
from pathlib import Path

from awep.fetcher import fetch_once
from awep.models import FetchRequest
from awep.storage import EvidenceStore
from awep.verify import verify_run


def test_verify_succeeds_and_detects_tampering(tmp_path: Path, httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://example.com/a",
        text="Example " * 80,
        headers={"content-type": "text/plain"},
    )
    store = EvidenceStore(tmp_path / ".awep")
    receipt = store.write_fetch_result(
        fetch_once(FetchRequest(url="https://example.com/a", run_id="run-test"))
    )
    assert verify_run("run-test", store).ok
    path = store.run_path("run-test") / "receipts" / f"{receipt.event_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["response"]["status_code"] = 500
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    result = verify_run("run-test", store)
    assert not result.ok
    assert receipt.event_id in result.failures[0]
