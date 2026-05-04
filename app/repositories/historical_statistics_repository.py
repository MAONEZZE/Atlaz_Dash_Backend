"""
Historical statistics repository — Supabase (Postgres).

Table schema assumption (pending stakeholder confirmation):
  Table: statistics_history
  Columns:
    id, date (timestamp), responsible (text), role (text: 'closer'|'sdr'),
    channel (text), product (text), stage (text), status (text),
    revenue_type (text), ticket_range (text), activity (text),
    -- SDR fields:
    conexoes_enviadas (int), conexoes_aceitas (int), abordagens (int),
    inmails_enviados (int), follow_ups (int), numeros_captados (int),
    ligacoes_agendadas (int), indicacoes_captadas (int),
    -- Closer fields:
    ligacoes_realizadas (int), reunioes_agendadas (int),
    reunioes_realizadas (int), indicacoes (int)

Until schema is confirmed, queries stub to return [].
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
    conditions: list[str] = []

    if start_date:
        conditions.append("date >= :start_date")
        params["start_date"] = start_date

    if end_date:
        conditions.append("date < :end_date")
        params["end_date"] = end_date

    for field_name, value in [
        ("channel", channel),
        ("responsible", responsible),
        ("product", product),
        ("stage", stage),
        ("status", status),
        ("revenue_type", revenue_type),
        ("ticket_range", ticket_range),
        ("activity", activity),
    ]:
        normalized = _normalize_filter(value)
        if normalized:
            # Use unaccent + lower for accent-insensitive compare (Postgres unaccent extension)
            # Fallback: lower(field) = lower(value) if unaccent not available
            conditions.append(f"lower(unaccent({field_name}::text)) = :{field_name}")
            params[field_name] = normalized

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    # STUB: Table name placeholder — replace with confirmed table name
    query = text(f"""
        SELECT
            responsible AS "Nome",
            role,
            SUM(conexoes_enviadas)    AS conexoes_enviadas,
            SUM(conexoes_aceitas)     AS conexoes_aceitas,
            SUM(abordagens)           AS abordagens,
            SUM(inmails_enviados)     AS inmails_enviados,
            SUM(follow_ups)           AS follow_ups,
            SUM(numeros_captados)     AS numeros_captados,
            SUM(ligacoes_agendadas)   AS ligacoes_agendadas,
            SUM(indicacoes_captadas)  AS indicacoes_captadas,
            SUM(ligacoes_realizadas)  AS ligacoes_realizadas,
            SUM(reunioes_agendadas)   AS reunioes_agendadas,
            SUM(reunioes_realizadas)  AS reunioes_realizadas,
            SUM(indicacoes)           AS indicacoes
        FROM statistics_history
        {where_clause}
        GROUP BY responsible, role
        ORDER BY responsible
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
