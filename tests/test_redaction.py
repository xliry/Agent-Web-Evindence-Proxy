from awep.redaction import REDACTED, redact_headers, redact_url


def test_redacts_secret_query_params() -> None:
    url = redact_url("https://example.com/path?token=abc&x=1&signature=zzz")
    assert f"token={REDACTED}" in url
    assert f"signature={REDACTED}" in url
    assert "x=1" in url
    assert "abc" not in url


def test_redacts_secret_headers() -> None:
    headers = redact_headers({"Authorization": "Bearer x", "Accept": "text/html"})
    assert headers["Authorization"] == REDACTED
    assert headers["Accept"] == "text/html"
