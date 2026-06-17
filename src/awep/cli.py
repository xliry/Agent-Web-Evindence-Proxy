from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from awep.fetcher import fetch_once
from awep.models import FetchRequest
from awep.report import build_and_write_report
from awep.storage import EvidenceStore
from awep.verify import verify_run

app = typer.Typer(help="Agent Web Evidence Proxy")
console = Console()
StorageRoot = Annotated[
    Path,
    typer.Option("--storage-root", envvar="AWE_PROXY_STORAGE_ROOT"),
]
Tags = Annotated[list[str] | None, typer.Option("--tag")]


@app.command()
def fetch(
    url: str,
    claim: str | None = None,
    run_id: str | None = None,
    agent_id: str = "manual",
    tool_name: str = "cli",
    citation_label: str | None = None,
    source_expected: str | None = None,
    tag: Tags = None,
    storage_root: StorageRoot = Path(".awep"),
    allow_private: bool = False,
) -> None:
    store = EvidenceStore(storage_root)
    request = FetchRequest(
        url=url,
        claim=claim,
        run_id=run_id,
        agent_id=agent_id,
        tool_name=tool_name,
        citation_label=citation_label,
        source_expected=source_expected,
        tags=tag or [],
    )
    receipt = store.write_fetch_result(fetch_once(request, allow_private=allow_private))
    console.print(
        f"[green]receipt[/green] {receipt.event_id} "
        f"status={receipt.quality.status} run={receipt.run_id}"
    )


@app.command()
def report(
    run_id: Annotated[str, typer.Argument()] = "latest",
    storage_root: StorageRoot = Path(".awep"),
) -> None:
    store = EvidenceStore(storage_root)
    resolved = store.resolve_run_id(run_id)
    path = build_and_write_report(resolved, store)
    console.print(f"[green]report[/green] {path}")


@app.command()
def verify(
    run_id: Annotated[str, typer.Argument()] = "latest",
    storage_root: StorageRoot = Path(".awep"),
) -> None:
    store = EvidenceStore(storage_root)
    resolved = store.resolve_run_id(run_id)
    result = verify_run(resolved, store)
    if not result.ok:
        for failure in result.failures:
            console.print(f"[red]failure[/red] {failure}")
        raise typer.Exit(1)
    console.print(f"[green]ok[/green] checked {result.checked_receipts} receipts")


@app.command("runs")
def list_runs(
    storage_root: StorageRoot = Path(".awep"),
) -> None:
    store = EvidenceStore(storage_root)
    table = Table("Run ID", "Created", "Updated", "Receipts")
    if store.runs_root.exists():
        for metadata_path in sorted(store.runs_root.glob("*/metadata.json")):
            import json

            data = json.loads(metadata_path.read_text(encoding="utf-8"))
            receipts = len(list((metadata_path.parent / "receipts").glob("*.json")))
            table.add_row(
                data["run_id"],
                data.get("created_at", ""),
                data.get("updated_at", ""),
                str(receipts),
            )
    console.print(table)


@app.command()
def show(
    run_id: Annotated[str, typer.Argument()] = "latest",
    storage_root: StorageRoot = Path(".awep"),
) -> None:
    store = EvidenceStore(storage_root)
    resolved = store.resolve_run_id(run_id)
    report_path = store.run_path(resolved) / "report.md"
    if not report_path.exists():
        report_path = build_and_write_report(resolved, store)
    console.print(report_path.read_text(encoding="utf-8"))


@app.command()
def serve(
    host: str = "127.0.0.1",
    port: int = 8787,
    storage_root: StorageRoot = Path(".awep"),
) -> None:
    import uvicorn

    from awep.server import create_app

    uvicorn.run(create_app(storage_root=storage_root), host=host, port=port)


if __name__ == "__main__":
    app()
