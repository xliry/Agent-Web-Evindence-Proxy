from pathlib import Path

from awep.extraction import extract_content


def fixture(name: str) -> bytes:
    return (Path(__file__).parent / "fixtures" / name).read_bytes()


def test_extracts_title_markdown_and_text() -> None:
    title, markdown, text = extract_content(fixture("normal.html"), "text/html")
    assert title == "Example Domain"
    assert "# Example Domain" in markdown
    assert "illustrative examples" in text
    assert len(text) > 500
