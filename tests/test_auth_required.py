import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.auth import require_auth
from app.schemas.auth_schema import AuthUserDTO

client = TestClient(app, raise_server_exceptions=False)

PROTECTED = [
    "/metrics",
    "/users",
    "/users/1/metrics",
    "/goals/fat",
    "/pre-sales/funnels",
]

@pytest.mark.parametrize("path", PROTECTED)
def test_endpoint_rejects_no_token(path):
    resp = client.get(path)
    assert resp.status_code == 401

@pytest.mark.parametrize("path", PROTECTED)
def test_endpoint_rejects_invalid_token(path):
    resp = client.get(path, headers={"Authorization": "Bearer badtoken"})
    assert resp.status_code == 401

def _mock_auth():
    return AuthUserDTO(id=1, user_id=1, nome="Test", cargo="closer", email="test@test.com", imagem_url=None)

@pytest.mark.parametrize("path", PROTECTED)
def test_endpoint_accepts_valid_token(path):
    app.dependency_overrides[require_auth] = _mock_auth
    try:
        resp = client.get(path)
        assert resp.status_code == 200
    finally:
        app.dependency_overrides.pop(require_auth, None)
