"""
Sales finance route — Phase 2 placeholder.
Returns safe empty contract until BASE_VENDAS wiring is complete.
"""
from datetime import datetime
import pytz
from fastapi import APIRouter

from app.dtos.sales_values_dto import (
    SalesFinanceResponseDTO,
    FinancialMonthDTO,
    MonthlyFinancialTableDTO,
)

router = APIRouter()

_MONTHS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
_TZ_BR = pytz.timezone("America/Sao_Paulo")


def _build_default_months() -> list[FinancialMonthDTO]:
    current_month = datetime.now(_TZ_BR).month
    return [
        FinancialMonthDTO(m=m, atual=(i + 1 == current_month))
        for i, m in enumerate(_MONTHS)
    ]


@router.get("/sales/finance", response_model=None)
async def sales_finance() -> dict:
    """
    Financial data for Vendas page.
    Phase 2 placeholder — returns safe empty contract.
    Real data sourced from BASE_VENDAS tab (wiring deferred).
    """
    current_month_idx = datetime.now(_TZ_BR).month - 1
    response = SalesFinanceResponseDTO(
        MESES_FIN=_build_default_months(),
        TABELA_FIN_MENSAL=MonthlyFinancialTableDTO(mesAtualIdx=current_month_idx),
    )
    return response.model_dump()
