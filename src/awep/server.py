from __future__ import annotations

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

    @app.get("/v1/runs/{run_id}/report.md")
    def report(run_id: str) -> Response:
        try:
            resolved = store.resolve_run_id(run_id)
            path = build_and_write_report(resolved, store)
            return Response(path.read_text(encoding="utf-8"), media_type="text/markdown")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/v1/runs/{run_id}/evidence.json")
    def evidence(run_id: str) -> Response:
        try:
            resolved = store.resolve_run_id(run_id)
            path = store.run_path(resolved) / "evidence.json"
            if not path.exists():
                build_and_write_report(resolved, store)
            return Response(path.read_text(encoding="utf-8"), media_type="application/json")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/v1/runs/{run_id}/verify")
    def verify(run_id: str) -> dict[str, object]:
        try:
            resolved = store.resolve_run_id(run_id)
            return verify_run(resolved, store).model_dump(mode="json")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return app


app = create_app()
