"""実アプリが認証より先にDBへアクセスしないことを確認する。"""

# Streamlit ElementListの動的な要素型はpylintが推論できない。
# pylint: disable=no-member

import sqlite3
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from streamlit.testing.v1 import AppTest

from backend.favorite import get_favorites_words
from backend.practice_history import list_attempts
from backend.users import get_or_create_google_user

APP_PATH = Path(__file__).resolve().parents[2] / "src" / "app.py"


def test_unconfigured_app_stops_before_tabs(tmp_path: Path) -> None:
    with patch.dict(
        "os.environ",
        {
            "USER_DB_PATH": str(tmp_path / "user.db"),
            "WORDS_DB_PATH": str(tmp_path / "words.db"),
        },
    ):
        with patch("streamlit.secrets", {}):
            app = AppTest.from_file(APP_PATH).run()
    assert not app.exception
    assert app.error
    assert not app.tabs
    assert not (tmp_path / "user.db").exists()
    assert not (tmp_path / "words.db").exists()


def test_authenticated_app_saves_for_current_account(
    tmp_path: Path, auth_settings: dict[str, Any]
) -> None:
    dictionary = tmp_path / "words.db"
    with sqlite3.connect(dictionary) as conn:
        conn.executescript(
            "CREATE TABLE words(word_id INTEGER, word TEXT); INSERT INTO words VALUES(1,'hello');"
            "CREATE TABLE meanings(word_id INTEGER, meaning TEXT, part_of_speech TEXT, category TEXT);"
            "CREATE TABLE word_explanations(word_id INTEGER, explanation TEXT);"
            "CREATE TABLE search_logs(word_id INTEGER PRIMARY KEY, count INTEGER);"
        )
    user = MagicMock()
    user.is_logged_in = True
    user.get.side_effect = {
        "sub": "account-a",
        "iss": "https://accounts.google.com",
    }.get
    with patch.dict(
        "os.environ",
        {"USER_DB_PATH": str(tmp_path / "user.db"), "WORDS_DB_PATH": str(dictionary)},
    ):
        with patch("streamlit.secrets", auth_settings), patch("streamlit.user", user):
            app = AppTest.from_file(APP_PATH).run()
            assert not app.exception
            first = get_or_create_google_user("account-a")
            app.button(key=f"tab6__{first}_favorite_hello").click().run()
            app.text_area[0].input("I drink coffee every morning.")
            app.button(
                key="FormSubmitter:composition_answer_form-回答を保存"
            ).click().run()
            assert not app.exception
            assert get_favorites_words(first) == ["hello"]
            assert len(list_attempts(first, "sentence_composition")) == 1
            user.get.side_effect = {
                "sub": "account-b",
                "iss": "https://accounts.google.com",
            }.get
            app.run()
            assert not app.exception
            second = get_or_create_google_user("account-b")
            assert get_favorites_words(second) == []
            assert not list_attempts(second, "sentence_composition")
            assert app.text_area[0].value == ""
