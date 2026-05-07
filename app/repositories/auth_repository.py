from datetime import datetime
from typing import Optional

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        if not settings.database_url:
            return None
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
    return _engine


def get_auth_user_by_email(email: str) -> dict | None:
    engine = _get_engine()
    if engine is None:
        return None
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT a.id, a.user_id, a.email, a.password_hash, a.is_active, a.last_login_at,
                           u.nome, u.cargo, u.imagem_url
                    FROM dash_auth_users a
                    LEFT JOIN dash_users u ON a.user_id = u.id
                    WHERE LOWER(a.email) = LOWER(:email)
                    LIMIT 1
                """),
                {"email": email},
            )
            row = result.fetchone()
            return dict(row._mapping) if row else None
    except SQLAlchemyError as exc:
        logger.warning("auth_repository: get_by_email DB error | detail={}", str(exc))
        return None


def update_last_login(auth_user_id: int) -> None:
    engine = _get_engine()
    if engine is None:
        return
    try:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE dash_auth_users SET last_login_at = NOW() WHERE id = :id"),
                {"id": auth_user_id},
            )
    except SQLAlchemyError as exc:
        logger.warning("auth_repository: update_last_login error | id={} | detail={}", auth_user_id, str(exc))


def create_refresh_token(
    user_id: int,
    token_hash: str,
    expires_at: datetime,
    user_agent: str | None,
    ip: str | None,
) -> None:
    engine = _get_engine()
    if engine is None:
        return
    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO dash_auth_refresh_tokens (user_id, token_hash, expires_at, user_agent, ip)
                    VALUES (:user_id, :token_hash, :expires_at, :user_agent, :ip)
                """),
                {"user_id": user_id, "token_hash": token_hash, "expires_at": expires_at,
                 "user_agent": user_agent, "ip": ip},
            )
    except SQLAlchemyError as exc:
        logger.warning("auth_repository: create_refresh_token error | detail={}", str(exc))


def get_refresh_token(token_hash: str) -> dict | None:
    engine = _get_engine()
    if engine is None:
        return None
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, user_id, token_hash, expires_at, revoked_at
                    FROM dash_auth_refresh_tokens
                    WHERE token_hash = :hash
                      AND revoked_at IS NULL
                      AND expires_at > NOW()
                    LIMIT 1
                """),
                {"hash": token_hash},
            )
            row = result.fetchone()
            return dict(row._mapping) if row else None
    except SQLAlchemyError as exc:
        logger.warning("auth_repository: get_refresh_token error | detail={}", str(exc))
        return None


def revoke_refresh_token(token_hash: str) -> None:
    engine = _get_engine()
    if engine is None:
        return
    try:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE dash_auth_refresh_tokens SET revoked_at = NOW() WHERE token_hash = :hash"),
                {"hash": token_hash},
            )
    except SQLAlchemyError as exc:
        logger.warning("auth_repository: revoke_refresh_token error | detail={}", str(exc))


def get_auth_user_by_id(auth_user_id: int) -> dict | None:
    engine = _get_engine()
    if engine is None:
        return None
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT a.id, a.user_id, a.email, a.password_hash, a.is_active,
                           u.nome, u.cargo, u.imagem_url
                    FROM dash_auth_users a
                    LEFT JOIN dash_users u ON a.user_id = u.id
                    WHERE a.id = :id
                    LIMIT 1
                """),
                {"id": auth_user_id},
            )
            row = result.fetchone()
            return dict(row._mapping) if row else None
    except SQLAlchemyError as exc:
        logger.warning("auth_repository: get_by_id error | id={} | detail={}", auth_user_id, str(exc))
        return None


def revoke_all_user_refresh_tokens(user_id: int) -> None:
    engine = _get_engine()
    if engine is None:
        return
    try:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE dash_auth_refresh_tokens SET revoked_at = NOW() WHERE user_id = :uid AND revoked_at IS NULL"),
                {"uid": user_id},
            )
    except SQLAlchemyError as exc:
        logger.warning("auth_repository: revoke_all error | user_id={} | detail={}", user_id, str(exc))
