"""
Pre-sales routes — Phase 2 placeholder.
Returns all five channels with zeroed values.
Real data wiring deferred to Phase 2.
"""
from fastapi import APIRouter

from app.dtos.pre_sales_dto import PreSalesResponseDTO

router = APIRouter()


@router.get("/pre-sales/funnels", response_model=None)
async def pre_sales_funnels() -> dict:
    """
    Return funnel data per channel for Pré-vendas page.
    Phase 2 placeholder — all channels present, values zeroed.
    """
    return PreSalesResponseDTO().model_dump()
