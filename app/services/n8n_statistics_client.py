from typing import Optional

import httpx
from loguru import logger

from app.core.config import settings


def _validate_shape(data: object) -> bool:
    if not isinstance(data, dict):
        return False
    if "SDR" not in data or "CLOSER" not in data:
        return False
    if not isinstance(data["SDR"], list) or not isinstance(data["CLOSER"], list):
        return False
    return True


async def fetch_current_month_statistics(
    data_inicio: Optional[int] = None,
    data_fim: Optional[int] = None,
    responsavel: Optional[int] = None,
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

    params: dict = {}
    if data_inicio is not None:
        params["data_inicio"] = data_inicio
    if data_fim is not None:
        params["data_fim"] = data_fim
    if responsavel is not None:
        params["responsavel"] = responsavel
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
