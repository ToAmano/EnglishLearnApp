"""Azureの永続保存先を初期化し、環境変数からOIDC設定を供給する。"""

import json
import os
import sqlite3
from collections.abc import Mapping
from contextlib import closing
from pathlib import Path


def _initialize_database(source: Path, target: Path) -> None:
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    seed = source / "database" / "user.db"
    if not seed.exists():
        with closing(sqlite3.connect(target)):
            return
    with closing(
        sqlite3.connect(seed.resolve().as_uri() + "?mode=ro", uri=True)
    ) as original:
        with closing(sqlite3.connect(target)) as persistent:
            original.backup(persistent)


GENERATED_HEADER = "# Generated from Azure environment variables.\n"


def _clear_generated_auth(config: Path) -> None:
    if config.exists() and config.read_text(encoding="utf-8").startswith(
        GENERATED_HEADER
    ):
        config.unlink()


def _write_auth_settings(source: Path, environment: Mapping[str, str]) -> None:
    names = ("OIDC_CLIENT_ID", "OIDC_CLIENT_SECRET", "OIDC_COOKIE_SECRET")
    if not all(environment.get(name, "").strip() for name in names):
        _clear_generated_auth(source / ".streamlit" / "secrets.toml")
        return
    redirect = environment.get("OIDC_REDIRECT_URI", "")
    if not redirect:
        host = environment.get("WEBSITE_HOSTNAME", "")
        if not host:
            raise ValueError("OIDC_REDIRECT_URI or WEBSITE_HOSTNAME is required")
        redirect = f"https://{host}/oauth2callback"
    settings = GENERATED_HEADER + (
        "[auth]\n"
        f"redirect_uri = {json.dumps(redirect)}\n"
        f"cookie_secret = {json.dumps(environment['OIDC_COOKIE_SECRET'])}\n\n"
        "[auth.google]\n"
        f"client_id = {json.dumps(environment['OIDC_CLIENT_ID'])}\n"
        f"client_secret = {json.dumps(environment['OIDC_CLIENT_SECRET'])}\n"
        'server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"\n'
        'client_kwargs = { scope = "openid profile email", prompt = "select_account" }\n'
    )
    directory = source / ".streamlit"
    directory.mkdir(parents=True, exist_ok=True)
    config = directory / "secrets.toml"
    descriptor = os.open(config, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(settings)
    config.chmod(0o600)


def configure_runtime(
    source: Path, target: Path, environment: Mapping[str, str]
) -> None:
    _initialize_database(source, target)
    _write_auth_settings(source, environment)


if __name__ == "__main__":
    configure_runtime(
        Path(__file__).resolve().parents[1],
        Path(os.environ["USER_DB_PATH"]),
        os.environ,
    )
