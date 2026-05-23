from omomuki.storage.markdown import normalize_markdown


def test_normalize_strips_bom_and_trailing_whitespace() -> None:
    raw = "\ufeff# Title  \r\n\r\nBody line  \n"
    assert normalize_markdown(raw) == "# Title\n\nBody line\n"
