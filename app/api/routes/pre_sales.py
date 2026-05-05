"""
Pre-sales routes — reads BASE_VENDAS tab.
"""
from typing import Optional

from fastapi import APIRouter, Query

from app.services.pre_sales_service import get_pre_sales_funnels

router = APIRouter()


@router.get("/pre-sales/funnels", response_model=None)
async def pre_sales_funnels(
    data_inicio: Optional[int] = Query(default=None, description="Início do período (timestamp ms)"),
    data_fim: Optional[int] = Query(default=None, description="Fim do período (timestamp ms)"),
) -> dict:
    """Funnel data per channel for Pré-vendas page. Reads BASE_VENDAS tab."""
    response = await get_pre_sales_funnels(data_inicio=data_inicio, data_fim=data_fim)
    return response.model_dump()
