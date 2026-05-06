from datetime import datetime, timezone
from typing import Optional

import httpx
import pytz
from loguru import logger

from app.core.config import settings

_TZ_BR = pytz.timezone("America/Sao_Paulo")


def _current_month_ms() -> tuple[int, int]:
    """Return (start_ms, end_ms) for current month in America/Sao_Paulo."""
    now_br = datetime.now(_TZ_BR)
    start_br = now_br.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return int(start_br.timestamp() * 1000), int(now_br.timestamp() * 1000)


def _validate_shape(data: object) -> bool:
    if not isinstance(data, dict):
        return False
    if "SDR" not in data or "CLOSER" not in data:
        return False
    if not isinstance(data["SDR"], list) or not isinstance(data["CLOSER"], list):
        return False
    return True


async def fetch_current_month_statistics(
    start_ms: Optional[int] = None,
    end_ms: Optional[int] = None,
    responsavel: Optional[int] = None,
    canal: Optional[str] = None,
    produto: Optional[str] = None,
    etapa_do_funil: Optional[str] = None,
    status_do_negocio: Optional[str] = None,
    tipo_de_receita: Optional[str] = None,
    faixa_de_ticket: Optional[str] = None,
    tipo_de_atividade: Optional[str] = None,
) -> dict:
    """Fetch statistics from n8n. Passes all filters as query params. Never raises."""
    url = settings.n8n_statistics_url
    timeout = float(settings.n8n_statistics_timeout_seconds)

    # n8n requires start_date and end_date; default to current month
    default_start, default_end = _current_month_ms()
    params: dict = {
        "start_date": start_ms if start_ms is not None else default_start,
        "end_date": end_ms if end_ms is not None else default_end,
    }
    if responsavel is not None:
        params["responsavel"] = responsavel
    if canal:
        params["canal"] = canal
    if produto:
        params["produto"] = produto
    if etapa_do_funil:
        params["etapa_do_funil"] = etapa_do_funil
    if status_do_negocio:
        params["status_do_negocio"] = status_do_negocio
    if tipo_de_receita:
        params["tipo_de_receita"] = tipo_de_receita
    if faixa_de_ticket:
        params["faixa_de_ticket"] = faixa_de_ticket
    if tipo_de_atividade:
        params["tipo_de_atividade"] = tipo_de_atividade

    empty: dict = {"SDR": [], "CLOSER": []}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException:
        logger.warning("n8n statistics: timeout after {}s | url={}", timeout, url)
        return empty
    except httpx.HTTPStatusError as exc:
        logger.warning("n8n statistics: HTTP {} | url={}", exc.response.status_code, url)
        return empty
    except httpx.RequestError as exc:
        logger.warning("n8n statistics: network error | type={} | detail={}", type(exc).__name__, str(exc))
        return empty
    except ValueError:
        logger.warning("n8n statistics: invalid JSON | url={}", url)
        return empty

    if not _validate_shape(data):
        logger.warning("n8n statistics: unexpected shape | keys={}", list(data.keys()) if isinstance(data, dict) else type(data))
        return empty

    return data
