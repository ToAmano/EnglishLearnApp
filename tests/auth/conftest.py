"""認証テスト専用の設定。実クライアント情報は使用しない。"""

from typing import Any

import pytest


@pytest.fixture
def auth_settings() -> dict[str, Any]:
    return {
        "auth": {
            "redirect_uri": "http://localhost:8501/oauth2callback",
            "cookie_secret": "test-cookie-secret",
            "google": {
                "client_id": "test-client",
                "client_secret": "test-client-secret",
                "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration",
            },
        }
    }
