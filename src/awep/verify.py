from __future__ import annotations

import json

from awep.models import VerifyResult
from awep.storage import EvidenceStore, compute_receipt_hash


def verify_run(run_id: str, store: EvidenceStore) -> VerifyResult:
    receipts = store.receipts(run_id)
    failures: list[str] = []
    previous: str | None = None
    for receipt in receipts:
        expected = compute_receipt_hash(receipt)
        if receipt.previous_receipt_hash != previous:
            failures.append(f"{receipt.event_id}: previous hash mismatch")
        if receipt.receipt_hash != expected:
            failures.append(f"{receipt.event_id}: receipt hash mismatch")
        previous = receipt.receipt_hash
    result = VerifyResult(
        ok=not failures,
        run_id=run_id,
        checked_receipts=len(receipts),
        failures=failures,
    )
    root = store.run_path(run_id)
    root.mkdir(parents=True, exist_ok=True)
    (root / "verify.json").write_text(
        json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return result
