from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.core.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str = Security(_api_key_header)) -> None:
    if not settings.sales_api_key:
        raise HTTPException(status_code=500, detail="API key not configured on server")
    if api_key != settings.sales_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
