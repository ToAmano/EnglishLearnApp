"""外部Google通信を置き換え、認証境界と実DBの動作を確認する。"""

# Streamlit ElementListの動的な要素型はpylintが推論できない。
# pylint: disable=no-member

import sqlite3
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from streamlit.testing.v1 import AppTest

SCRIPT = "from auth.oidc import require_google_login\nimport streamlit as st\nst.write(require_google_login())"


def identity(
    subject: object = "subject-a",
    logged_in: bool = True,
    issuer: str = "https://accounts.google.com",
) -> MagicMock:
    user = MagicMock()
    user.is_logged_in = logged_in
    user.get.side_effect = {"sub": subject, "iss": issuer, "name": "Learner"}.get
    return user


@pytest.fixture(autouse=True)
def temporary_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USER_DB_PATH", str(tmp_path / "user.db"))


def test_logged_out_stops_before_database(
    tmp_path: Path, auth_settings: dict[str, Any]
) -> None:
    with (
        patch("streamlit.user", identity(logged_in=False)),
        patch("streamlit.secrets", auth_settings),
    ):
        app = AppTest.from_string(SCRIPT).run()
    assert not app.exception
    assert len(app.button) == 1
    assert not app.markdown
    assert not (tmp_path / "user.db").exists()


def test_missing_config_stops(tmp_path: Path) -> None:
    with patch("streamlit.user", identity()), patch("streamlit.secrets", {}):
        app = AppTest.from_string(SCRIPT).run()
    assert not app.exception
    assert app.error
    assert not (tmp_path / "user.db").exists()


@pytest.mark.parametrize("subject", [None, "", " ", 123])
def test_invalid_subject_stops(
    subject: object, tmp_path: Path, auth_settings: dict[str, Any]
) -> None:
    with (
        patch("streamlit.user", identity(subject)),
        patch("streamlit.secrets", auth_settings),
    ):
        app = AppTest.from_string(SCRIPT).run()
    assert not app.exception
    assert app.error
    assert not (tmp_path / "user.db").exists()


def test_wrong_issuer_stops(tmp_path: Path, auth_settings: dict[str, Any]) -> None:
    with (
        patch("streamlit.user", identity(issuer="https://other.example")),
        patch("streamlit.secrets", auth_settings),
    ):
        app = AppTest.from_string(SCRIPT).run()
    assert not app.exception
    assert app.error
    assert not (tmp_path / "user.db").exists()


def test_account_switch_clears_state(
    tmp_path: Path, auth_settings: dict[str, Any]
) -> None:
    app = AppTest.from_string(SCRIPT)
    with patch("streamlit.secrets", auth_settings):
        with patch("streamlit.user", identity()):
            app.run()
            first_id = app.markdown[0].value
            app.session_state["composition_answer"] = "private answer"
            app.run()
            assert app.session_state["composition_answer"] == "private answer"
        with patch("streamlit.user", identity("subject-b")):
            app.run()
            assert "composition_answer" not in app.session_state
            assert app.markdown[0].value != first_id
    assert not app.exception
    with sqlite3.connect(tmp_path / "user.db") as conn:
        assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 2


def test_database_error_is_redacted(auth_settings: dict[str, Any]) -> None:
    with patch("streamlit.user", identity()), patch("streamlit.secrets", auth_settings):
        with patch(
            "backend.users.get_or_create_google_user",
            side_effect=sqlite3.OperationalError("secret-detail"),
        ):
            app = AppTest.from_string(SCRIPT).run()
    assert not app.exception
    assert app.error
    assert "secret-detail" not in app.error[0].value


def test_logout_clears_state() -> None:
    script = "from auth.oidc import logout\nimport streamlit as st\nst.session_state['private'] = 'answer'\nlogout()"
    with patch("streamlit.logout") as provider_logout:
        app = AppTest.from_string(script).run()
    assert not app.exception
    assert "private" not in app.session_state
    provider_logout.assert_called_once()
