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
from app.utils.normalize_text import normalize_for_compare

# Intentionally lazy — engine created only if DATABASE_URL is set
_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        if not settings.database_url:
            return None
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
    return _engine


def _normalize_filter(value: Optional[str]) -> Optional[str]:
    if not value or not value.strip():
        return None
    return normalize_for_compare(value.strip())


def fetch_historical_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    channel: Optional[str] = None,
    responsible: Optional[str] = None,
    product: Optional[str] = None,
    stage: Optional[str] = None,
    status: Optional[str] = None,
    revenue_type: Optional[str] = None,
    ticket_range: Optional[str] = None,
    activity: Optional[str] = None,
) -> list[dict]:
    """
    Query historical statistics from Supabase Postgres.
    Returns [] if DB unavailable or no rows match.
    All text filters are accent+case insensitive.

    NOTE: Stubbed until Supabase table schema is confirmed.
    When schema is ready, replace the stub body with real query.
    """
    engine = _get_engine()
    if engine is None:
        logger.warning("historical_statistics_repository: DATABASE_URL not set — returning empty")
        return []

    params: dict = {}

    # Build WHERE clause — date filter + responsible name filter
    date_conditions = []
    if start_date:
        date_conditions.append("m.data_referente >= :start_date")
        params["start_date"] = start_date
    if end_date:
        date_conditions.append("m.data_referente < :end_date")
        params["end_date"] = end_date

    responsible_filter = ""
    if responsible:
        normalized_responsible = _normalize_filter(responsible)
        if normalized_responsible:
            responsible_filter = "AND lower(unaccent(u.nome::text)) = :responsible"
            params["responsible"] = normalized_responsible

    date_where = ("WHERE " + " AND ".join(date_conditions)) if date_conditions else "WHERE TRUE"

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
        {date_where}
        {responsible_filter}
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
