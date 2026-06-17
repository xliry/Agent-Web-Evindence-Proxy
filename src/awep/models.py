from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

QualityStatus = Literal["ok", "blocked", "empty", "login_required", "js_required", "error"]
ClaimStatus = Literal["supported", "weak", "missing", "blocked", "empty", "error"]


class FetchRequest(BaseModel):
    url: str
    method: str = "GET"
    claim: str | None = None
    run_id: str | None = None
    agent_id: str = "manual"
    tool_name: str = "cli"
    citation_label: str | None = None
    source_expected: str | None = None
    tags: list[str] = Field(default_factory=list)


class RequestEvidence(BaseModel):
    method: str
    url: str
    url_sha256: str


class ResponseEvidence(BaseModel):
    status_code: int | None = None
    final_url: str | None = None
    redirect_count: int = 0
    content_type: str | None = None
    body_sha256: str | None = None
    error: str | None = None


class ExtractionEvidence(BaseModel):
    title: str | None = None
    markdown_path: str | None = None
    text_path: str | None = None
    text_sha256: str | None = None
    text_chars: int = 0
    markdown_chars: int = 0


class QualityEvidence(BaseModel):
    status: QualityStatus
    flags: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class ClaimEvidence(BaseModel):
    text: str
    status: ClaimStatus
    score: float = 0.0
    snippet: str | None = None
    matched_terms: list[str] = Field(default_factory=list)


class Receipt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    event_id: str
    run_id: str
    agent_id: str
    tool_name: str
    created_at: str
    request: RequestEvidence
    response: ResponseEvidence
    extraction: ExtractionEvidence
    quality: QualityEvidence
    claim: ClaimEvidence | None = None
    citation_label: str | None = None
    source_expected: str | None = None
    tags: list[str] = Field(default_factory=list)
    previous_receipt_hash: str | None = None
    receipt_hash: str | None = None


class FetchResult(BaseModel):
    request: FetchRequest
    receipt: Receipt
    markdown: str = ""
    text: str = ""


class EventRecord(BaseModel):
    event_type: str
    event_id: str
    run_id: str
    created_at: str
    receipt_path: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class VerifyResult(BaseModel):
    ok: bool
    run_id: str
    checked_receipts: int
    failures: list[str] = Field(default_factory=list)
