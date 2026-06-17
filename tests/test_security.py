import pytest

from awep.security import UnsafeUrlError, assert_url_safe


@pytest.mark.parametrize(
    "url",
    [
        "file:///tmp/x",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://10.0.0.1",
        "http://169.254.169.254/latest/meta-data",
    ],
)
def test_blocks_unsafe_urls(url: str) -> None:
    with pytest.raises(UnsafeUrlError):
        assert_url_safe(url)


def test_allow_private_allows_local_testing() -> None:
    assert_url_safe("http://127.0.0.1:8000", allow_private=True)
