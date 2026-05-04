import re
from typing import Optional

from app.core.config import settings
from app.core.field_maps import resolve_name
from app.dtos.goals_dto import SalesGoalsDTO
from app.dtos.users_dto import UserInfoDTO
from app.utils.normalize_text import normalize_for_compare

# Known users with their image token env-key suffix
_IMAGE_TOKEN_KEYS: dict[str, str] = {
    "jacob": "jacob",
    "jonathan": "jonathan",
    "alex": "alex",
    "jennifer": "jennifer",
    "tayrone": "tayrone",
}

_BASE_IMAGE_URL = "https://storage.googleapis.com/atlaz-dash-images/{name}.jpg"


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalize_for_compare(name)).strip("-")


def _image_url(canonical_name: str) -> str:
    key = normalize_for_compare(canonical_name)
    token_key = _IMAGE_TOKEN_KEYS.get(key)
    if not token_key:
        return ""
    token = settings.image_token_for(token_key)
    if not token:
        return ""
    return f"{_BASE_IMAGE_URL.format(name=token_key)}?token={token}"


def get_users(goals: list[SalesGoalsDTO]) -> list[UserInfoDTO]:
    seen: set[str] = set()
    users: list[UserInfoDTO] = []
    for g in goals:
        canonical = resolve_name(g.Nome)
        slug = _slugify(canonical)
        if slug in seen:
            continue
        seen.add(slug)
        cargo = g.Cargo.lower() if g.Cargo else ""
        users.append(UserInfoDTO(
            id=slug,
            nome=canonical,
            cargo=cargo,
            imagem_url=_image_url(canonical),
        ))
    return users


def get_user_by_id(user_id: str) -> Optional[UserInfoDTO]:
    """Return a UserInfoDTO for a known user slug, or None if unknown."""
    for canonical, token_key in _IMAGE_TOKEN_KEYS.items():
        if _slugify(resolve_name(canonical)) == user_id or canonical == user_id:
            resolved = resolve_name(canonical)
            return UserInfoDTO(
                id=user_id,
                nome=resolved,
                cargo="",
                imagem_url=_image_url(resolved),
            )
    return None
