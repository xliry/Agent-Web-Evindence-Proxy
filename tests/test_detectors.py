from pathlib import Path

import pytest

from awep.claims import evaluate_claim_against_text
from awep.detectors import classify_quality
from awep.extraction import decode_body, extract_content


def classify_fixture(name: str):
    body = (Path(__file__).parent / "fixtures" / name).read_bytes()
    title, _markdown, text = extract_content(body, "text/html")
    return classify_quality(200, title, text, decode_body(body), "text/html")


@pytest.mark.parametrize(
    ("name", "status", "flag"),
    [
        ("normal.html", "ok", None),
        ("captcha.html", "blocked", "captcha"),
        ("login.html", "login_required", "login_wall_text"),
        ("real_login_wall.html", "login_required", "login_wall_text"),
        ("github_public_repo.html", "ok", "login_link_present"),
        ("empty.html", "empty", "low_text_chars"),
        ("js_required.html", "js_required", "enable_javascript_text"),
    ],
)
def test_classifies_fixtures(name: str, status: str, flag: str | None) -> None:
    quality = classify_fixture(name)
    assert quality.status == status
    if flag:
        assert flag in quality.flags


@pytest.mark.parametrize("status_code", [403, 429])
def test_blocked_http_statuses(status_code: int) -> None:
    quality = classify_quality(status_code, "Denied", "Access denied " * 30, "", "text/html")
    assert quality.status == "blocked"
    assert f"http_{status_code}" in quality.flags


def test_http_401_is_login_required() -> None:
    quality = classify_quality(401, "Unauthorized", "Authentication required", "", "text/html")
    assert quality.status == "login_required"
    assert "http_401" in quality.flags
    assert "login_wall_text" in quality.flags


def test_github_public_page_claim_is_not_blocked_by_login_nav() -> None:
    body = (Path(__file__).parent / "fixtures" / "github_public_repo.html").read_bytes()
    title, _markdown, text = extract_content(body, "text/html")
    quality = classify_quality(200, title, text, decode_body(body), "text/html")
    claim = evaluate_claim_against_text(
        "The repository documents an agent evidence proxy with hash-chain verification.",
        text,
        quality,
    )
    assert quality.status == "ok"
    assert "login_link_present" in quality.flags
    assert claim is not None
    assert claim.status in {"supported", "weak"}
