from typing import Optional

from app.core.config import settings
from app.dtos.users_dto import UserInfoDTO
from app.repositories.users_repository import fetch_all_users, fetch_user_by_id
from app.utils.normalize_text import normalize_for_compare

_IMAGE_TOKEN_KEYS: dict[str, str] = {
    "jacob": "jacob",
    "jonathan": "jonathan",
    "alex": "alex",
    "jennifer": "jennifer",
    "tayrone": "tayrone",
}

_BASE_IMAGE_URL = "https://storage.googleapis.com/atlaz-dash-images/{name}.jpg"


def _image_url(nome: str) -> str:
    key = normalize_for_compare(nome)
    token_key = _IMAGE_TOKEN_KEYS.get(key)
    if not token_key:
        return ""
    token = settings.image_token_for(token_key)
    if not token:
        return ""
    return f"{_BASE_IMAGE_URL.format(name=token_key)}?token={token}"


def _normalize_cargo(raw: str) -> str:
    from app.utils.normalize_text import normalize_for_compare
    v = normalize_for_compare(raw)
    if "sdr" in v or "pre" in v:
        return "SDR"
    if "closer" in v or "vendedor" in v:
        return "Closer"
    return raw.strip().title()


def _row_to_dto(row: dict) -> UserInfoDTO:
    nome = str(row.get("nome") or "")
    cargo = _normalize_cargo(str(row.get("cargo") or ""))
    imagem = str(row.get("imagem_url") or "") or _image_url(nome)
    return UserInfoDTO(
        id=str(row["id"]),
        nome=nome,
        cargo=cargo,
        imagem_url=imagem,
    )


def get_users(_ignored=None) -> list[UserInfoDTO]:
    """Return all users from dash_users table."""
    rows = fetch_all_users()
    return [_row_to_dto(r) for r in rows]


def get_user_by_id(user_id: str) -> Optional[UserInfoDTO]:
    """Return user by dash_users.id (numeric string)."""
    try:
        uid = int(user_id)
    except (ValueError, TypeError):
        return None
    row = fetch_user_by_id(uid)
    if not row:
        return None
    return _row_to_dto(row)
