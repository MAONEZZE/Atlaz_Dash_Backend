"""Pre-sales routes — funnel data per channel."""
from typing import Annotated

from fastapi import APIRouter, Depends
from loguru import logger

from app.core.auth import require_auth
from app.dtos.pre_sales_dto import PreSalesResponseDTO
from app.schemas.filters_schema import FunnelFilters
from app.services.pre_sales_service import get_pre_sales_funnels

router = APIRouter()


@router.get("/pre-sales/funnels", response_model=None, dependencies=[Depends(require_auth)])
async def pre_sales_funnels(
    filters: Annotated[FunnelFilters, Depends()],
) -> dict:
    """Funnel data per channel for Pré-vendas page."""
    try:
        data = await get_pre_sales_funnels(
            data_inicio=filters.data_inicio,
            data_fim=filters.data_fim,
        )
        return data
    except Exception as exc:
        logger.warning("pre-sales/funnels: error | type={} | detail={}", type(exc).__name__, str(exc))
        return PreSalesResponseDTO().model_dump()
