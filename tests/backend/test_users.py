"""ユーザー識別と旧データ保持を一時DBで検証する。"""

import sqlite3
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path

import pytest

from backend.core.user_schema import initialize_user_schema
from backend.practice_history import (
    Attempt,
    get_self_evaluations,
    initialize_history,
    list_attempts,
    save_attempt,
    save_self_evaluation,
)
from backend.users import get_or_create_google_user


@pytest.fixture(name="user_db")
def user_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "user.db"
    monkeypatch.setenv("USER_DB_PATH", str(path))
    return path


def test_same_subject_returns_same_user_id(user_db: Path) -> None:
    first = get_or_create_google_user("google-subject-a")
    assert first == get_or_create_google_user("google-subject-a")
    assert first != get_or_create_google_user("google-subject-b")
    assert user_db.exists()


def test_concurrent_creation_is_unique(user_db: Path) -> None:
    with ThreadPoolExecutor(max_workers=4) as executor:
        identifiers = list(
            executor.map(get_or_create_google_user, ["same-subject"] * 8)
        )
    assert len(set(identifiers)) == 1
    with sqlite3.connect(user_db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1


def test_initialize_preserves_legacy_data(user_db: Path) -> None:
    with sqlite3.connect(user_db) as conn:
        conn.executescript(
            "CREATE TABLE favorites(word TEXT PRIMARY KEY); INSERT INTO favorites VALUES('old');"
            "CREATE TABLE vocab_status(word TEXT, status TEXT); INSERT INTO vocab_status VALUES('old','active');"
        )
    initialize_user_schema()
    initialize_user_schema()
    with sqlite3.connect(user_db) as conn:
        assert conn.execute("SELECT * FROM favorites").fetchall() == [("old",)]
        assert conn.execute("SELECT * FROM vocab_status").fetchall() == [
            ("old", "active")
        ]


@pytest.mark.parametrize("subject", ["", " ", "\t"])
def test_invalid_subject_rejected(user_db: Path, subject: str) -> None:
    with pytest.raises(ValueError):
        get_or_create_google_user(subject)
    assert not user_db.exists()


def test_initialize_preserves_legacy_history(user_db: Path) -> None:
    initialize_history()
    save_attempt(
        Attempt(
            "old-attempt",
            "default_user",
            "sentence_composition",
            {"prompt": "old"},
            {"text": "old answer"},
        )
    )
    save_self_evaluation("old-attempt", "default_user", "できた")
    before = list_attempts("default_user", "sentence_composition")
    account = get_or_create_google_user("new-account")
    initialize_user_schema()
    assert list_attempts("default_user", "sentence_composition") == before
    assert get_self_evaluations("old-attempt", "default_user") == ["できた"]
    assert list_attempts(account, "sentence_composition") == []
    assert user_db.exists()
