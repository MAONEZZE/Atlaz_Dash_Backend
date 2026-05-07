from fastapi import APIRouter, Depends, Request, Response

from app.core.auth import require_auth
from app.core.limiter import limiter
from app.schemas.auth_schema import AuthUserDTO, LoginRequest, RefreshRequest, TokenResponse
from app.services.auth_service import get_current_user_info, login, logout, refresh

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def auth_login(request: Request, body: LoginRequest) -> TokenResponse:
    """Authenticate with email + password. Returns JWT access + refresh tokens."""
    user_agent = request.headers.get("user-agent")
    ip = request.client.host if request.client else None
    return login(body.email, body.password, user_agent=user_agent, ip=ip)


@router.post("/refresh", response_model=TokenResponse)
async def auth_refresh(body: RefreshRequest, request: Request) -> TokenResponse:
    """Exchange a valid refresh token for a new token pair (rotation)."""
    user_agent = request.headers.get("user-agent")
    ip = request.client.host if request.client else None
    return refresh(body.refresh_token, user_agent=user_agent, ip=ip)


@router.post("/logout", status_code=204)
async def auth_logout(body: RefreshRequest) -> Response:
    """Revoke the given refresh token."""
    logout(body.refresh_token)
    return Response(status_code=204)


@router.get("/me", response_model=AuthUserDTO)
async def auth_me(current_user: AuthUserDTO = Depends(require_auth)) -> AuthUserDTO:
    """Return the currently authenticated user."""
    return current_user
