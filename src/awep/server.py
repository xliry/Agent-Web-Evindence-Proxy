from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response

from awep.fetcher import fetch_once
from awep.models import FetchRequest
from awep.report import build_and_write_report
from awep.storage import EvidenceStore
from awep.verify import verify_run


def create_app(storage_root: Path | str = ".awep") -> FastAPI:
    app = FastAPI(title="Agent Web Evidence Proxy")
    store = EvidenceStore(storage_root)

    def resolve_existing_run_id(run_id: str) -> str:
        resolved = store.resolve_run_id(run_id)
        if not store.run_path(resolved).exists():
            raise FileNotFoundError(f"run not found: {resolved}")
        return resolved

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/fetch")
    def fetch(request: FetchRequest, allow_private: bool = False) -> dict[str, object]:
        receipt = store.write_fetch_result(fetch_once(request, allow_private=allow_private))
        return {
            "run_id": receipt.run_id,
            "event_id": receipt.event_id,
            "quality_status": receipt.quality.status,
            "claim_status": receipt.claim.status if receipt.claim else None,
            "receipt_hash": receipt.receipt_hash,
        }

    @app.get("/v1/runs")
    def runs() -> dict[str, object]:
        items: list[dict[str, object]] = []
        if store.runs_root.exists():
            for metadata_path in sorted(store.runs_root.glob("*/metadata.json")):
                try:
                    data = json.loads(metadata_path.read_text(encoding="utf-8"))
                    receipts = len(list((metadata_path.parent / "receipts").glob("*.json")))
                    items.append(
                        {
                            "run_id": data["run_id"],
                            "created_at": data.get("created_at"),
                            "updated_at": data.get("updated_at"),
                            "receipt_count": receipts,
                        }
                    )
                except (OSError, KeyError, json.JSONDecodeError):
                    continue
        return {"runs": items}

    @app.get("/v1/runs/{run_id}/report.md")
    def report(run_id: str) -> Response:
        try:
            resolved = resolve_existing_run_id(run_id)
            path = build_and_write_report(resolved, store)
            return Response(path.read_text(encoding="utf-8"), media_type="text/markdown")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/v1/runs/{run_id}/report")
    def regenerate_report(run_id: str) -> dict[str, object]:
        try:
            resolved = resolve_existing_run_id(run_id)
            path = build_and_write_report(resolved, store)
            return {"run_id": resolved, "report_path": str(path), "ok": True}
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/v1/runs/{run_id}/evidence.json")
    def evidence(run_id: str) -> Response:
        try:
            resolved = resolve_existing_run_id(run_id)
            path = store.run_path(resolved) / "evidence.json"
            if not path.exists():
                build_and_write_report(resolved, store)
            return Response(path.read_text(encoding="utf-8"), media_type="application/json")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/v1/runs/{run_id}/verify")
    def verify(run_id: str) -> dict[str, object]:
        return verify_json(run_id)

    @app.post("/v1/runs/{run_id}/verify")
    def verify_json(run_id: str) -> dict[str, object]:
        try:
            resolved = resolve_existing_run_id(run_id)
            return verify_run(resolved, store).model_dump(mode="json")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return app


app = create_app()
