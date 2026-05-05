"""
Sales finance route — reads BASE_VENDAS tab.
"""
from fastapi import APIRouter

from app.services.finance_service import get_sales_finance_data

router = APIRouter()


@router.get("/sales/finance", response_model=None)
async def sales_finance() -> dict:
    """Financial data for Vendas page. Reads BASE_VENDAS tab."""
    response = get_sales_finance_data()
    return response.model_dump()
