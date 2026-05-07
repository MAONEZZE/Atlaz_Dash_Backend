from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_bearer = HTTPBearer(auto_error=False)


async def require_api_key(api_key: str = Security(_api_key_header)) -> None:
    if not settings.sales_api_key:
        raise HTTPException(status_code=500, detail="API key not configured on server")
    if api_key != settings.sales_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


async def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
):
    """JWT bearer token dependency. Returns AuthUserDTO or raises 401."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authorization header required")
    from app.services.auth_service import get_current_user_info
    return get_current_user_info(credentials.credentials)
