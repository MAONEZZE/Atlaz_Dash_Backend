"""
Historical statistics repository — Supabase (Postgres).

Joins dash_metricas_prospeccao (metrics) with dash_users (user info).
Aggregates _atual columns by user and date range.
Maps dashboard fields to API response field names.
"""

from datetime import datetime
from typing import Optional

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings

# Intentionally lazy — engine created only if DATABASE_URL is set
_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        if not settings.database_url:
            return None
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
    return _engine


def fetch_historical_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: Optional[int] = None,
) -> list[dict]:
    """
    Query historical statistics from Supabase Postgres.
    Returns [] if DB unavailable or no rows match.
    """
    engine = _get_engine()
    if engine is None:
        logger.warning("historical_statistics_repository: DATABASE_URL not set — returning empty")
        return []

    params: dict = {}
    conditions: list[str] = ["TRUE"]

    if start_date:
        conditions.append("m.data_referente >= :start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append("m.data_referente < :end_date")
        params["end_date"] = end_date
    if user_id is not None:
        conditions.append("m.id_user = :user_id")
        params["user_id"] = user_id

    where_clause = "WHERE " + " AND ".join(conditions)

    query = text(f"""
        SELECT
            u.nome AS "Nome",
            u.cargo AS role,
            SUM(COALESCE(m.conexoes_atual, 0))          AS conexoes_enviadas,
            SUM(COALESCE(m.conexoes_aceitas_atual, 0))  AS conexoes_aceitas,
            SUM(COALESCE(m.abordagens_atual, 0))        AS abordagens,
            SUM(COALESCE(m.inmail_atual, 0))            AS inmails_enviados,
            SUM(COALESCE(m.follow_up_atual, 0))         AS follow_ups,
            SUM(COALESCE(m.numero_atual, 0))            AS numeros_captados,
            SUM(COALESCE(m.lig_agendado_atual, 0))      AS ligacoes_agendadas,
            SUM(COALESCE(m.lig_realizado_atual, 0))     AS ligacoes_realizadas,
            SUM(COALESCE(m.reuniao_agendado_atual, 0))  AS reunioes_agendadas,
            SUM(COALESCE(m.reuniao_realizado_atual, 0)) AS reunioes_realizadas,
            SUM(COALESCE(m.indicacoes_atual, 0))        AS indicacoes
        FROM dash_metricas_prospeccao m
        JOIN dash_users u ON m.id_user = u.id
        {where_clause}
        GROUP BY u.id, u.nome, u.cargo
        ORDER BY u.nome
    """)

    try:
        with engine.connect() as conn:
            result = conn.execute(query, params)
            rows = [dict(row._mapping) for row in result]
            return rows
    except SQLAlchemyError as exc:
        logger.warning("historical_statistics_repository: DB error | type={} | detail={}", type(exc).__name__, str(exc))
        return []
    except Exception as exc:
        logger.warning("historical_statistics_repository: unexpected error | type={} | detail={}", type(exc).__name__, str(exc))
        return []
