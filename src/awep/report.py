from __future__ import annotations

import json
from collections import Counter
from html import escape
from pathlib import Path

from awep.models import Receipt
from awep.storage import EvidenceStore
from awep.util import compact, utc_now_str
from awep.verify import verify_run


def build_and_write_report(run_id: str, store: EvidenceStore) -> Path:
    receipts = store.receipts(run_id)
    root = store.run_path(run_id)
    verification = verify_run(run_id, store)
    markdown = render_markdown(run_id, receipts, verification.ok)
    (root / "report.md").write_text(markdown, encoding="utf-8")
    evidence = {
        "schema_version": 1,
        "run_id": run_id,
        "generated_at": utc_now_str(),
        "verification": verification.model_dump(mode="json"),
        "receipts": [receipt.model_dump(mode="json") for receipt in receipts],
    }
    (root / "evidence.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return root / "report.md"


def render_markdown(run_id: str, receipts: list[Receipt], verified: bool) -> str:
    quality_counts = Counter(receipt.quality.status for receipt in receipts)
    claim_counts = Counter(receipt.claim.status for receipt in receipts if receipt.claim)
    created = receipts[0].created_at if receipts else ""
    updated = receipts[-1].created_at if receipts else ""
    lines = [
        "# Agent Web Evidence Report",
        "",
        f"Run ID: {run_id}",
        f"Created: {created}",
        f"Updated: {updated}",
        f"Receipts: {len(receipts)}",
        f"Verification: {'ok' if verified else 'failed'}",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total fetches | {len(receipts)} |",
        f"| OK | {quality_counts['ok']} |",
        f"| Blocked | {quality_counts['blocked']} |",
        f"| Empty | {quality_counts['empty']} |",
        f"| Login required | {quality_counts['login_required']} |",
        f"| JavaScript required | {quality_counts['js_required']} |",
        f"| Errors | {quality_counts['error']} |",
        f"| Claims supported | {claim_counts['supported']} |",
        f"| Claims weak | {claim_counts['weak']} |",
        f"| Claims missing lexical match | {claim_counts['missing']} |",
        "",
        "## Source Health",
        "",
        "| Time | Status | HTTP | URL | Title | Flags |",
        "|------|--------|------|-----|-------|-------|",
    ]
    for receipt in receipts:
        lines.append(
            "| "
            + " | ".join(
                md_cell(value)
                for value in [
                    receipt.created_at,
                    receipt.quality.status,
                    str(receipt.response.status_code or ""),
                    receipt.request.url,
                    receipt.extraction.title or "",
                    ", ".join(receipt.quality.flags),
                ]
            )
            + " |"
        )
    lines += [
        "",
        "## Claim Evidence",
        "",
        "Claim status describes lexical overlap with extracted text, not whether the source "
        "was fetched or readable. Check Source Health for source availability.",
        "",
        "| Claim | Evidence Status | Score | URL | Snippet |",
        "|-------|-----------------|-------|-----|---------|",
    ]
    for receipt in receipts:
        if receipt.claim:
            lines.append(
                "| "
                + " | ".join(
                    md_cell(value)
                    for value in [
                        receipt.claim.text,
                        receipt.claim.status,
                        f"{receipt.claim.score:.3f}",
                        receipt.request.url,
                        compact(receipt.claim.snippet, 260),
                    ]
                )
                + " |"
            )
    lines += ["", "## Blocked or Low-Quality Sources", ""]
    low_quality = [r for r in receipts if r.quality.status != "ok"]
    if not low_quality:
        lines.append("None.")
    for receipt in low_quality:
        lines.append(
            f"- `{receipt.event_id}` {receipt.quality.status}: {receipt.request.url} "
            f"({', '.join(receipt.quality.flags) or 'no flags'})"
        )
    lines += ["", "## Receipts", ""]
    for receipt in receipts:
        lines += [
            f"### {receipt.event_id}",
            "",
            f"- URL: {receipt.request.url}",
            f"- Final URL: {receipt.response.final_url or ''}",
            f"- Status code: {receipt.response.status_code or ''}",
            f"- Quality status: {receipt.quality.status}",
            f"- Receipt hash: `{receipt.receipt_hash}`",
            f"- Previous hash: `{receipt.previous_receipt_hash or ''}`",
            f"- Markdown snapshot: `{receipt.extraction.markdown_path or ''}`",
            f"- Text snapshot: `{receipt.extraction.text_path or ''}`",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def md_cell(value: object) -> str:
    text = compact(str(value or ""), 220)
    return escape(text.replace("|", "\\|"))
