from __future__ import annotations

import httpx

from awep.claims import evaluate_claim_against_text
from awep.detectors import classify_quality
from awep.extraction import decode_body, extract_content
from awep.models import (
    ExtractionEvidence,
    FetchRequest,
    FetchResult,
    Receipt,
    RequestEvidence,
    ResponseEvidence,
)
from awep.redaction import redact_url
from awep.security import UnsafeUrlError, assert_url_safe
from awep.util import make_event_id, make_run_id, sha256_bytes, sha256_text, utc_now_str

USER_AGENT = "AgentWebEvidenceProxy/0.1 (+local evidence recorder; no bypass)"


def fetch_once(request: FetchRequest, allow_private: bool = False) -> FetchResult:
    run_id = request.run_id or make_run_id()
    event_id = make_event_id()
    safe_url = redact_url(request.url)
    request_ev = RequestEvidence(
        method=request.method.upper(),
        url=safe_url,
        url_sha256=sha256_text(request.url),
    )
    try:
        assert_url_safe(request.url, allow_private=allow_private)
        with httpx.Client(
            follow_redirects=True,
            timeout=20.0,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            response = client.request(request_ev.method, request.url)
        content_type = response.headers.get("content-type")
        title, markdown, text = extract_content(response.content, content_type)
        body_preview = decode_body(response.content)
        response_ev = ResponseEvidence(
            status_code=response.status_code,
            final_url=redact_url(str(response.url)),
            redirect_count=len(response.history),
            content_type=content_type,
            body_sha256=sha256_bytes(response.content),
        )
        quality = classify_quality(
            response.status_code,
            title,
            text,
            body_preview,
            content_type,
            redirect_count=len(response.history),
        )
    except (httpx.HTTPError, UnsafeUrlError, ValueError) as exc:
        title, markdown, text = None, "", ""
        response_ev = ResponseEvidence(error=str(exc))
        quality = classify_quality(None, None, "", "", None, error=str(exc))
    extraction = ExtractionEvidence(
        title=title,
        text_sha256=sha256_text(text),
        text_chars=len(text),
        markdown_chars=len(markdown),
    )
    claim = evaluate_claim_against_text(request.claim, text, quality)
    receipt = Receipt(
        event_id=event_id,
        run_id=run_id,
        agent_id=request.agent_id,
        tool_name=request.tool_name,
        created_at=utc_now_str(),
        request=request_ev,
        response=response_ev,
        extraction=extraction,
        quality=quality,
        claim=claim,
        citation_label=request.citation_label,
        source_expected=request.source_expected,
        tags=request.tags,
    )
    return FetchResult(request=request, receipt=receipt, markdown=markdown, text=text)
