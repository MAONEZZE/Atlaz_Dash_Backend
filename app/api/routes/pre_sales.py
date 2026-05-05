"""
Pre-sales routes — reads BASE_VENDAS tab.
"""
from fastapi import APIRouter

from app.services.pre_sales_service import get_pre_sales_funnels

router = APIRouter()


@router.get("/pre-sales/funnels", response_model=None)
async def pre_sales_funnels() -> dict:
    """Funnel data per channel for Pré-vendas page. Reads BASE_VENDAS tab."""
    response = get_pre_sales_funnels()
    return response.model_dump()
