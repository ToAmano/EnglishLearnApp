"""同じ単語に対する二人の操作と旧データを分離する。"""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from backend.core.db_core import get_user_db_connection
from backend.favorite import get_favorites_words, is_favorited, toggle_favorite
from backend.users import get_or_create_google_user
from backend.vocab_status import get_vocab_status, set_vocab_status


@pytest.fixture(name="accounts")
def create_accounts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[str, str]:
    monkeypatch.setenv("USER_DB_PATH", str(tmp_path / "user.db"))
    return get_or_create_google_user("a"), get_or_create_google_user("b")


def test_favorites_are_isolated(accounts: tuple[str, str]) -> None:
    first, second = accounts
    toggle_favorite("hello", first)
    assert is_favorited("hello", first)
    assert get_favorites_words(second) == []
    toggle_favorite("hello", second)
    toggle_favorite("hello", first)
    assert get_favorites_words(first) == []
    assert get_favorites_words(second) == ["hello"]


def test_status_is_isolated(accounts: tuple[str, str]) -> None:
    first, second = accounts
    assert get_vocab_status("hello", first) == "unknown"
    set_vocab_status("hello", "active", first)
    set_vocab_status("hello", "passive", second)
    assert get_vocab_status("hello", first) == "active"
    assert get_vocab_status("hello", second) == "passive"
    with pytest.raises(ValueError):
        set_vocab_status("hello", "invalid", first)


def test_unregistered_user_cannot_write(accounts: tuple[str, str]) -> None:
    assert accounts
    with pytest.raises(sqlite3.IntegrityError):
        toggle_favorite("hello", "missing")
    with pytest.raises(sqlite3.IntegrityError):
        set_vocab_status("hello", "active", "missing")


def test_legacy_vocabulary_is_not_exposed(accounts: tuple[str, str]) -> None:
    with closing(get_user_db_connection()) as conn:
        with conn:
            conn.executescript(
                "CREATE TABLE favorites(word TEXT PRIMARY KEY); INSERT INTO favorites VALUES('legacy');"
                "CREATE TABLE vocab_status(word TEXT, status TEXT); INSERT INTO vocab_status VALUES('legacy','active');"
            )
    for account in accounts:
        assert get_favorites_words(account) == []
        assert get_vocab_status("legacy", account) == "unknown"
