"""
Pre-sales routes — proxies n8n pre-sale/funels endpoint.
"""
from typing import Optional

import httpx
from fastapi import APIRouter, Query
from loguru import logger

from app.core.config import settings
from app.dtos.pre_sales_dto import PreSalesResponseDTO

router = APIRouter()


@router.get("/pre-sales/funnels", response_model=None)
async def pre_sales_funnels(
    data_inicio: Optional[int] = Query(default=None, description="Início do período (timestamp ms)"),
    data_fim: Optional[int] = Query(default=None, description="Fim do período (timestamp ms)"),
) -> dict:
    """Funnel data per channel for Pré-vendas page. Proxies n8n pre-sale/funels webhook."""
    url = settings.n8n_pre_sales_url
    timeout = float(settings.n8n_statistics_timeout_seconds)
    params: dict = {}
    if data_inicio is not None:
        params["data_inicio"] = data_inicio
    if data_fim is not None:
        params["data_fim"] = data_fim

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        if isinstance(data, dict):
            return data
        logger.warning("pre-sales/funnels: unexpected response type={}", type(data))
    except httpx.TimeoutException:
        logger.warning("pre-sales/funnels: timeout | url={}", url)
    except httpx.HTTPStatusError as exc:
        logger.warning("pre-sales/funnels: HTTP {} | url={}", exc.response.status_code, url)
    except Exception as exc:
        logger.warning("pre-sales/funnels: error | type={} | detail={}", type(exc).__name__, str(exc))

    return PreSalesResponseDTO().model_dump()
