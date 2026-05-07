# Security Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 3 security/bug issues: add JWT auth to unprotected sensitive endpoints, fix user-not-found bug leaking all stats, and add rate limiting to login.

**Architecture:** (1) Add `Depends(require_auth)` to four routers using the already-implemented `require_auth` in `app/core/auth.py`. (2) Return empty `NormalizedStatistics()` instead of full stats when user_id not found in DB. (3) Wire `slowapi` Limiter into FastAPI app and apply a 5/min decorator to the login route.

**Tech Stack:** FastAPI, slowapi, python-jose, pytest, httpx

---

### Task 1: Fix `_filter_by_user_id` bug — returns full stats for unknown user_id

**Files:**
- Modify: `app/services/statistics_service.py:186-189`
- Test: `tests/test_statistics_service.py`

**Step 1: Write the failing test**

Create `tests/test_statistics_service.py`:

```python
import pytest
from unittest.mock import patch
from app.services.statistics_service import (
    NormalizedStatistics,
    NormalizedCloserStats,
    _filter_by_user_id,
)

def _full_stats():
    return NormalizedStatistics(
        closer=[NormalizedCloserStats(nome="Jacob", ligacoes_realizadas=5)],
        sdr=[],
    )

def test_filter_by_user_id_unknown_returns_empty():
    with patch("app.services.statistics_service.fetch_user_by_id", return_value=None):
        result = _filter_by_user_id(_full_stats(), 999)
    assert result.closer == []
    assert result.sdr == []

def test_filter_by_user_id_known_filters_correctly():
    with patch("app.services.statistics_service.fetch_user_by_id", return_value={"nome": "Jacob"}):
        result = _filter_by_user_id(_full_stats(), 1)
    assert len(result.closer) == 1
    assert result.closer[0].nome == "Jacob"
```

**Step 2: Run test — must FAIL**

```bash
pytest tests/test_statistics_service.py -v
```
Expected: `test_filter_by_user_id_unknown_returns_empty` FAILS (returns full stats, not empty)

**Step 3: Fix `_filter_by_user_id`**

In `app/services/statistics_service.py`, line 188–189 — change:
```python
        logger.warning("_filter_by_user_id: user_id={} not found in DB — returning unfiltered stats", user_id)
        return stats
```
To:
```python
        logger.warning("_filter_by_user_id: user_id={} not found in DB — returning empty stats", user_id)
        return NormalizedStatistics()
```

**Step 4: Run test — must PASS**

```bash
pytest tests/test_statistics_service.py -v
```
Expected: both tests PASS

**Step 5: Commit**

```bash
git add tests/test_statistics_service.py app/services/statistics_service.py
git commit -m "fix: return empty stats when user_id not found in _filter_by_user_id"
```

---

### Task 2: Add JWT auth to sensitive endpoints

**Files:**
- Modify: `app/api/routes/metrics.py`
- Modify: `app/api/routes/users.py`
- Modify: `app/api/routes/goals.py`
- Modify: `app/api/routes/pre_sales.py`

**Step 1: Write failing integration tests**

Create `tests/test_auth_required.py`:

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app

client = TestClient(app, raise_server_exceptions=False)

PROTECTED = [
    "/metrics",
    "/users",
    "/users/1/metrics",
    "/goals/fat",
    "/pre-sales/funnels",
]

@pytest.mark.parametrize("path", PROTECTED)
def test_endpoint_requires_auth_without_token(path):
    resp = client.get(path)
    assert resp.status_code == 401

@pytest.mark.parametrize("path", PROTECTED)
def test_endpoint_requires_auth_invalid_token(path):
    resp = client.get(path, headers={"Authorization": "Bearer badtoken"})
    assert resp.status_code == 401
```

**Step 2: Run tests — must FAIL**

```bash
pytest tests/test_auth_required.py -v
```
Expected: all FAIL with 200 (routes currently public)

**Step 3: Add `require_auth` to metrics route**

In `app/api/routes/metrics.py`:
```python
from fastapi import APIRouter, Depends
from app.core.auth import require_auth
from app.schemas.auth_schema import AuthUserDTO
# ... existing imports ...

@router.get("/metrics", response_model=None, dependencies=[Depends(require_auth)])
async def metrics(
    filters: Annotated[DashboardFilters, Depends()],
) -> dict:
    # ... unchanged body ...
```

**Step 4: Add `require_auth` to users routes**

In `app/api/routes/users.py`:
```python
from app.core.auth import require_auth
# ... existing imports ...

@router.get("/users", response_model=None, dependencies=[Depends(require_auth)])
async def list_users() -> dict:
    # ... unchanged body ...

@router.get("/users/{user_id}/metrics", response_model=None, dependencies=[Depends(require_auth)])
async def user_metrics(
    user_id: int,
    filters: Annotated[DashboardFilters, Depends()],
) -> dict:
    # ... unchanged body ...
```

**Step 5: Add `require_auth` to goals route**

In `app/api/routes/goals.py`:
```python
from fastapi import APIRouter, Depends
from app.core.auth import require_auth
# ... existing imports ...

@router.get("/goals/fat", response_model=None, dependencies=[Depends(require_auth)])
async def get_goals_fat() -> dict:
    # ... unchanged body ...
```

**Step 6: Add `require_auth` to pre-sales route**

In `app/api/routes/pre_sales.py`:
```python
from fastapi import APIRouter, Depends
from app.core.auth import require_auth
# ... existing imports ...

@router.get("/pre-sales/funnels", response_model=None, dependencies=[Depends(require_auth)])
async def pre_sales_funnels(
    filters: Annotated[FunnelFilters, Depends()],
) -> dict:
    # ... unchanged body ...
```

**Step 7: Run tests — must PASS**

```bash
pytest tests/test_auth_required.py -v
```
Expected: all PASS with 401

**Step 8: Commit**

```bash
git add app/api/routes/metrics.py app/api/routes/users.py app/api/routes/goals.py app/api/routes/pre_sales.py tests/test_auth_required.py
git commit -m "feat: require JWT auth on metrics, users, goals, and pre-sales endpoints"
```

---

### Task 3: Rate limiting on `/auth/login`

**Files:**
- Modify: `requirements.txt`
- Modify: `app/main.py`
- Modify: `app/api/routes/auth.py`
- Test: `tests/test_rate_limit.py`

**Step 1: Add slowapi to requirements**

In `requirements.txt`, add:
```
slowapi>=0.1.9
```

**Step 2: Install**

```bash
pip install slowapi
```

**Step 3: Wire Limiter into app**

In `app/main.py`, add after the existing imports:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**Step 4: Apply rate limit to login route**

In `app/api/routes/auth.py`:
```python
from fastapi import APIRouter, Depends, Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.auth import require_auth
from app.schemas.auth_schema import AuthUserDTO, LoginRequest, RefreshRequest, TokenResponse
from app.services.auth_service import get_current_user_info, login, logout, refresh

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def auth_login(request: Request, body: LoginRequest) -> TokenResponse:
    """Authenticate with email + password. Returns JWT access + refresh tokens."""
    user_agent = request.headers.get("user-agent")
    ip = request.client.host if request.client else None
    return login(body.email, body.password, user_agent=user_agent, ip=ip)
```

Note: `request: Request` must be the first parameter for slowapi to work.

**Step 5: Write rate limit test**

Create `tests/test_rate_limit.py`:

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app, raise_server_exceptions=False)

def test_login_rate_limit():
    bad_body = {"email": "x@x.com", "password": "wrong"}
    responses = []
    # slowapi default uses in-memory store; 5 allowed, 6th triggers 429
    for _ in range(6):
        resp = client.post("/auth/login", json=bad_body)
        responses.append(resp.status_code)
    # First 5 return 401 (bad creds), 6th returns 429
    assert responses[:5] == [401] * 5
    assert responses[5] == 429
```

**Step 6: Run test**

```bash
pytest tests/test_rate_limit.py -v
```
Expected: PASS (6th request → 429)

**Step 7: Commit**

```bash
git add requirements.txt app/main.py app/api/routes/auth.py tests/test_rate_limit.py
git commit -m "feat: add 5/min rate limit to /auth/login via slowapi"
```

---

### Task 4: Smoke test full flow

**Step 1: Restart server**

```bash
kill $(lsof -ti:8000); sleep 1
source venv/bin/activate && nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/uvicorn.log 2>&1 &
sleep 3
```

**Step 2: Verify auth required**

```bash
curl -s http://localhost:8000/metrics        # expect 401
curl -s http://localhost:8000/users          # expect 401
curl -s http://localhost:8000/goals/fat      # expect 401
curl -s http://localhost:8000/pre-sales/funnels  # expect 401
```

**Step 3: Verify /health still public**

```bash
curl -s http://localhost:8000/health  # expect {"status":"ok"}
```
