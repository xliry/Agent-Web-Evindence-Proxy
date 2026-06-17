from awep.fetcher import fetch_once
from awep.models import FetchRequest


def test_fetcher_normalizes_http_response(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://example.com",
        html=(
            "<title>Example Domain</title><p>"
            "Example Domain is used for illustrative examples. "
            + "x " * 250
            + "</p>"
        ),
    )
    result = fetch_once(
        FetchRequest(
            url="https://example.com",
            claim="Example Domain is used for illustrative examples",
        )
    )
    assert result.receipt.response.status_code == 200
    assert result.receipt.extraction.title == "Example Domain"
    assert result.receipt.quality.status == "ok"
    assert result.receipt.claim is not None
    assert result.receipt.claim.status == "supported"


def test_fetcher_records_unsafe_url_as_error() -> None:
    result = fetch_once(FetchRequest(url="http://127.0.0.1:8000"))
    assert result.receipt.quality.status == "error"
    assert "blocked private" in (result.receipt.response.error or "")
