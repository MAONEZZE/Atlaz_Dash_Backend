"""Sales finance route — reads BASE_VENDAS tab."""
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import require_api_key
from app.schemas.filters_schema import SalesFilters
from app.services.finance_service import get_sales_finance_data

router = APIRouter()


@router.get("/sales/values", response_model=None, dependencies=[Depends(require_api_key)])
async def sales_finance(
    filters: Annotated[SalesFilters, Depends()],
) -> dict:
    """Financial data for Vendas page. Reads BASE_VENDAS tab."""
    response = get_sales_finance_data(
        data_inicio=filters.data_inicio,
        data_fim=filters.data_fim,
        canal=filters.canal,
        produto=filters.produto,
    )
    return response.model_dump()
