from __future__ import annotations

import json
from pathlib import Path

from awep.models import EventRecord, FetchResult, Receipt
from awep.util import canonical_json, make_run_id, sha256_text, utc_now_str, validate_safe_id


class EvidenceStore:
    def __init__(self, storage_root: Path | str = ".awep") -> None:
        self.storage_root = Path(storage_root)
        self.runs_root = self.storage_root / "runs"

    def run_path(self, run_id: str) -> Path:
        return self.runs_root / validate_safe_id(run_id, "run id")

    def ensure_run(self, run_id: str | None = None) -> str:
        actual = run_id or make_run_id()
        validate_safe_id(actual, "run id")
        root = self.run_path(actual)
        (root / "receipts").mkdir(parents=True, exist_ok=True)
        (root / "snapshots").mkdir(parents=True, exist_ok=True)
        metadata = root / "metadata.json"
        now = utc_now_str()
        if metadata.exists():
            data = json.loads(metadata.read_text(encoding="utf-8"))
            data["updated_at"] = now
        else:
            data = {"run_id": actual, "created_at": now, "updated_at": now}
        metadata.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        return actual

    def resolve_run_id(self, run_id: str) -> str:
        if run_id != "latest":
            return validate_safe_id(run_id, "run id")
        if not self.runs_root.exists():
            raise FileNotFoundError("no runs found")
        candidates: list[tuple[str, str]] = []
        for metadata in self.runs_root.glob("*/metadata.json"):
            try:
                data = json.loads(metadata.read_text(encoding="utf-8"))
                candidates.append(
                    (data.get("updated_at") or data.get("created_at") or "", data["run_id"])
                )
            except (OSError, KeyError, json.JSONDecodeError):
                continue
        if not candidates:
            raise FileNotFoundError("no runs found")
        return sorted(candidates)[-1][1]

    def write_fetch_result(self, result: FetchResult) -> Receipt:
        receipt = result.receipt.model_copy(deep=True)
        run_id = self.ensure_run(receipt.run_id)
        receipt.run_id = run_id
        root = self.run_path(run_id)
        event_id = validate_safe_id(receipt.event_id, "event id")
        receipt.extraction.markdown_path = f"snapshots/{event_id}.md"
        receipt.extraction.text_path = f"snapshots/{event_id}.txt"
        (root / receipt.extraction.markdown_path).write_text(result.markdown, encoding="utf-8")
        (root / receipt.extraction.text_path).write_text(result.text, encoding="utf-8")
        receipt.previous_receipt_hash = self.latest_receipt_hash(run_id)
        receipt.receipt_hash = compute_receipt_hash(receipt)
        receipt_path = root / "receipts" / f"{event_id}.json"
        if receipt_path.exists():
            raise FileExistsError(f"receipt already exists: {event_id}")
        receipt_path.write_text(
            json.dumps(receipt.model_dump(mode="json"), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        self.append_event(
            EventRecord(
                event_type="fetch",
                event_id=event_id,
                run_id=run_id,
                created_at=receipt.created_at,
                receipt_path=f"receipts/{event_id}.json",
                data={
                    "quality_status": receipt.quality.status,
                    "claim_status": receipt.claim.status if receipt.claim else None,
                },
            )
        )
        self.touch_run(run_id)
        return receipt

    def append_event(self, event: EventRecord) -> None:
        root = self.run_path(event.run_id)
        with (root / "events.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.model_dump(mode="json"), sort_keys=True) + "\n")

    def touch_run(self, run_id: str) -> None:
        metadata = self.run_path(run_id) / "metadata.json"
        data = json.loads(metadata.read_text(encoding="utf-8"))
        data["updated_at"] = utc_now_str()
        metadata.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    def receipts(self, run_id: str) -> list[Receipt]:
        root = self.run_path(run_id) / "receipts"
        if not root.exists():
            return []
        receipts = [
            Receipt.model_validate_json(path.read_text(encoding="utf-8-sig"))
            for path in sorted(root.glob("*.json"))
        ]
        return sorted(receipts, key=lambda receipt: receipt.created_at)

    def latest_receipt_hash(self, run_id: str) -> str | None:
        receipts = self.receipts(run_id)
        return receipts[-1].receipt_hash if receipts else None


def compute_receipt_hash(receipt: Receipt) -> str:
    data = receipt.model_dump(mode="json")
    data["receipt_hash"] = None
    return sha256_text(canonical_json(data))
