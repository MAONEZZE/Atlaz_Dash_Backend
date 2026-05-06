"""
Sales finance route — reads BASE_VENDAS tab.
"""
from typing import Optional

from fastapi import APIRouter, Query

from app.services.finance_service import get_sales_finance_data

router = APIRouter()


@router.get("/sales/values", response_model=None)
async def sales_finance(
    data_inicio: Optional[int] = Query(default=None, description="Início do período (timestamp ms)"),
    data_fim: Optional[int] = Query(default=None, description="Fim do período (timestamp ms)"),
    canal: Optional[str] = Query(default=None, description="Canal de origem"),
    produto: Optional[str] = Query(default=None, description="Produto"),
) -> dict:
    """Financial data for Vendas page. Reads BASE_VENDAS tab."""
    response = get_sales_finance_data(
        data_inicio=data_inicio,
        data_fim=data_fim,
        canal=canal,
        produto=produto,
    )
    return response.model_dump()
