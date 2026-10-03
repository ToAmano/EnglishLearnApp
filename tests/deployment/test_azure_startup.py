"""Azure起動時の永続DBと秘密設定を一時ディレクトリで検証する。"""

import sqlite3
from pathlib import Path

import toml

from deployment.azure_startup import configure_runtime


def test_persistent_database_is_seeded_once(tmp_path: Path) -> None:
    source = tmp_path / "src"
    (source / "database").mkdir(parents=True)
    with sqlite3.connect(source / "database/user.db") as conn:
        conn.execute("CREATE TABLE favorites(word TEXT)")
        conn.execute("INSERT INTO favorites VALUES ('old')")
    target = tmp_path / "persistent/user.db"
    configure_runtime(source, target, {})
    with sqlite3.connect(target) as conn:
        conn.execute("INSERT INTO favorites VALUES ('new')")
    configure_runtime(source, target, {})
    with sqlite3.connect(target) as conn:
        assert conn.execute("SELECT word FROM favorites").fetchall() == [
            ("old",),
            ("new",),
        ]
    assert not (source / ".streamlit/secrets.toml").exists()


def test_environment_secrets_become_valid_toml(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    target = tmp_path / "persistent/user.db"
    environment = {
        "OIDC_CLIENT_ID": "test-id",
        "OIDC_CLIENT_SECRET": 'secret"with\\escapes',
        "OIDC_COOKIE_SECRET": "cookie-secret",
        "WEBSITE_HOSTNAME": "test.azurewebsites.net",
    }
    configure_runtime(source, target, environment)
    config = source / ".streamlit/secrets.toml"
    settings = toml.loads(config.read_text())
    assert (
        settings["auth"]["redirect_uri"]
        == "https://test.azurewebsites.net/oauth2callback"
    )
    assert settings["auth"]["google"]["client_secret"] == 'secret"with\\escapes'
    assert config.stat().st_mode & 0o777 == 0o600


def test_removed_environment_clears_generated_auth(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    target = tmp_path / "persistent/user.db"
    configure_runtime(
        source,
        target,
        {
            "OIDC_CLIENT_ID": "test-id",
            "OIDC_CLIENT_SECRET": "secret",
            "OIDC_COOKIE_SECRET": "cookie",
            "WEBSITE_HOSTNAME": "test.azurewebsites.net",
        },
    )
    configure_runtime(source, target, {})
    assert not (source / ".streamlit/secrets.toml").exists()
