from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException

from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_refresh_token,
    verify_password,
)
from app.core.config import settings
from app.repositories.auth_repository import (
    create_refresh_token,
    get_auth_user_by_email,
    get_auth_user_by_id,
    get_refresh_token,
    revoke_refresh_token,
    update_last_login,
)
from app.schemas.auth_schema import AuthUserDTO, TokenResponse


def _build_user_dto(row: dict) -> AuthUserDTO:
    return AuthUserDTO(
        id=row["id"],
        user_id=row["user_id"],
        nome=row.get("nome") or "",
        cargo=row.get("cargo") or "",
        email=row["email"],
        imagem_url=row.get("imagem_url"),
    )


def _issue_tokens(auth_user_id: int, user_dto: AuthUserDTO, user_agent: Optional[str], ip: Optional[str]) -> TokenResponse:
    access = create_access_token({"sub": str(auth_user_id), "email": user_dto.email})
    refresh = generate_refresh_token()
    refresh_hash = hash_refresh_token(refresh)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)
    create_refresh_token(auth_user_id, refresh_hash, expires_at, user_agent, ip)
    return TokenResponse(access_token=access, refresh_token=refresh, user=user_dto)


def login(email: str, password: str, user_agent: Optional[str] = None, ip: Optional[str] = None) -> TokenResponse:
    row = get_auth_user_by_email(email)
    if not row or not verify_password(password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    if not row.get("is_active", True):
        raise HTTPException(status_code=401, detail="Usuário inativo")
    update_last_login(row["id"])
    return _issue_tokens(row["id"], _build_user_dto(row), user_agent, ip)


def refresh(refresh_token_str: str, user_agent: Optional[str] = None, ip: Optional[str] = None) -> TokenResponse:
    token_hash = hash_refresh_token(refresh_token_str)
    token_row = get_refresh_token(token_hash)
    if not token_row:
        raise HTTPException(status_code=401, detail="Refresh token inválido ou expirado")

    revoke_refresh_token(token_hash)

    auth_user_id = token_row["user_id"]
    user_row = get_auth_user_by_id(auth_user_id)
    if not user_row:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    return _issue_tokens(auth_user_id, _build_user_dto(user_row), user_agent, ip)


def logout(refresh_token_str: str) -> None:
    token_hash = hash_refresh_token(refresh_token_str)
    revoke_refresh_token(token_hash)


def get_current_user_info(token: str) -> AuthUserDTO:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    auth_user_id_str = payload.get("sub")
    if not auth_user_id_str:
        raise HTTPException(status_code=401, detail="Token inválido")
    row = get_auth_user_by_id(int(auth_user_id_str))
    if not row or not row.get("is_active", True):
        raise HTTPException(status_code=401, detail="Usuário não encontrado ou inativo")
    return _build_user_dto(row)
