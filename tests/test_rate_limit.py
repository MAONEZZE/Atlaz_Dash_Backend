import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.limiter import limiter

client = TestClient(app, raise_server_exceptions=False)


def test_login_rate_limit_triggers_after_5_attempts():
    # Reset limiter state to ensure a clean counter for this test
    limiter.reset()  # clears all in-memory counters
    bad_body = {"email": "ratelimit@test.com", "password": "wrong"}
    statuses = [client.post("/auth/login", json=bad_body).status_code for _ in range(6)]
    assert statuses[:5] == [401] * 5
    assert statuses[5] == 429
