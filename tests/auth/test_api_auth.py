"""未認証の旧APIが学習データを返さないことを確認する。"""

from fastapi.testclient import TestClient

from api import app


def test_favorites_api_rejects_unauthenticated_requests() -> None:
    with TestClient(app) as client:
        for path in ("/api/favorites", "/api/favorites?user_id=default_user"):
            response = client.get(path)
            assert response.status_code == 403
            assert "favorites" not in response.json()
