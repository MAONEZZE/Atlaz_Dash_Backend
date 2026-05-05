"""
Users repository — reads from dash_users Supabase table.
Returns real integer IDs for use in other filters.
"""

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


def fetch_all_users() -> list[dict]:
    """Return all rows from dash_users. Returns [] on DB unavailable."""
    engine = _get_engine()
    if engine is None:
        logger.warning("users_repository: DATABASE_URL not set — returning empty")
        return []
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT id, nome, cargo, imagem_url FROM dash_users ORDER BY nome"))
            return [dict(row._mapping) for row in result]
    except SQLAlchemyError as exc:
        logger.warning("users_repository: DB error | type={} | detail={}", type(exc).__name__, str(exc))
        return []
    except Exception as exc:
        logger.warning("users_repository: unexpected error | type={} | detail={}", type(exc).__name__, str(exc))
        return []


def fetch_user_by_id(user_id: int) -> dict | None:
    """Return a single user by id, or None if not found."""
    engine = _get_engine()
    if engine is None:
        return None
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, nome, cargo, imagem_url FROM dash_users WHERE id = :uid LIMIT 1"),
                {"uid": user_id},
            )
            row = result.fetchone()
            return dict(row._mapping) if row else None
    except SQLAlchemyError as exc:
        logger.warning("users_repository: fetch_user_by_id DB error | id={} | detail={}", user_id, str(exc))
        return None
    except Exception as exc:
        logger.warning("users_repository: fetch_user_by_id error | id={} | detail={}", user_id, str(exc))
        return None
