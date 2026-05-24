import pytest

from sayane.cli.i18n import resolve_locale, set_locale


@pytest.fixture(autouse=True)
def _reset_locale() -> None:
    set_locale("en")
    yield
    set_locale("en")


def test_resolve_locale_prefers_sayane_lang(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAYANE_LANG", "ja")
    monkeypatch.setenv("LANG", "en_US.UTF-8")
    assert resolve_locale() == "ja"


def test_resolve_locale_falls_back_to_lang(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAYANE_LANG", raising=False)
    monkeypatch.setenv("LANG", "ja_JP.UTF-8")
    assert resolve_locale() == "ja"


def test_resolve_locale_ignores_lc_all_when_sayane_lang_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SAYANE_LANG", raising=False)
    monkeypatch.delenv("LANG", raising=False)
    monkeypatch.setenv("LC_ALL", "ja_JP.UTF-8")
    assert resolve_locale() == "en"


def test_resolve_locale_explicit_overrides_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAYANE_LANG", "ja")
    monkeypatch.setenv("LANG", "ja_JP.UTF-8")
    assert resolve_locale("en") == "en"
