"""
Finance service — reads BASE_VENDAS, returns SalesFinanceResponseDTO.
"""

from datetime import datetime, timezone
from typing import Optional

from loguru import logger

from app.core.config import settings
from app.dtos.sales_values_dto import (
    ChannelRevenueDTO,
    FinancialBreakdownDTO,
    FinancialMonthDTO,
    FinancialSummaryDTO,
    MonthlyFinancialTableDTO,
    MonthlyFinancialTableRowDTO,
    ProductRevenueDTO,
    ProductsTotalDTO,
    SalesFinanceResponseDTO,
)
from app.services.base_vendas_parser import (
    MONTH_NAMES,
    SaleRecord,
    filter_records,
    parse_base_vendas,
)
from app.services.google_sheets_service import read_tab
from app.utils.normalize_text import normalize_for_compare

# ── colors ────────────────────────────────────────────────────────────────────
_PRODUCT_COLORS: dict[str, str] = {
    "keepside": "#6366F1",
    "produto de aceleracao": "#10B981",
    "produto de ativacao": "#F59E0B",
    "produto de entrada": "#3B82F6",
}
_CHANNEL_COLORS: dict[str, str] = {
    "linkedin": "#0A66C2",
    "instagram": "#E1306C",
    "indicacao": "#8B5CF6",
    "whatsapp": "#25D366",
    "evento": "#F97316",
    "outros": "#6B7280",
}
_DEFAULT_COLOR = "#6B7280"


def _product_color(nome: str) -> str:
    return _PRODUCT_COLORS.get(normalize_for_compare(nome), _DEFAULT_COLOR)


def _channel_color(nome: str) -> str:
    return _CHANNEL_COLORS.get(normalize_for_compare(nome), _DEFAULT_COLOR)


# ── helpers ───────────────────────────────────────────────────────────────────

def _current_month_idx() -> int:
    return datetime.now(tz=timezone.utc).month - 1  # 0-based


def _safe_pct(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator * 100, 2)


# ── aggregators ───────────────────────────────────────────────────────────────

def _build_resumo(ganho: list[SaleRecord], em_neg: list[SaleRecord]) -> FinancialSummaryDTO:
    bruto     = sum(r.bruto for r in ganho)
    liquido   = sum(r.liquido_final for r in ganho)
    vendas    = len(ganho)
    taxa_plat = sum(r.taxa_entrada + r.taxa_restante for r in ganho)
    imposto   = sum(r.imposto for r in ganho)
    com_sdr   = sum(r.comissao_sdr_liq for r in ganho)
    com_clos  = sum(r.comissao_closer_liq for r in ganho)

    return FinancialSummaryDTO(
        bruto=round(bruto, 2),
        liquido=round(liquido, 2),
        vendido=round(bruto, 2),
        vendas=vendas,
        taxaPlataforma=round(taxa_plat, 2),
        ticketMedio=round(bruto / vendas, 2) if vendas else 0.0,
        margem=_safe_pct(liquido, bruto),
        comissaoSDR=round(com_sdr, 2),
        comissaoCloser=round(com_clos, 2),
        comissaoTotal=round(com_sdr + com_clos, 2),
        margemOpValor=round(liquido - com_sdr - com_clos, 2),
        emNegociacaoValor=round(sum(r.bruto for r in em_neg), 2),
        emNegociacaoQtd=len(em_neg),
        # deltas require a prior-period comparison — left 0 until filter context is added
        deltaLiquido=0.0,
        deltaBruto=0.0,
        deltaVendas=0.0,
        deltaMargem=0.0,
    )


def _build_meses_fin(ganho: list[SaleRecord]) -> list[FinancialMonthDTO]:
    cur_idx = _current_month_idx()
    result = []
    for i, nome in enumerate(MONTH_NAMES):
        bruto_m   = sum(r.bruto_mensal[i] for r in ganho)
        receita_m = sum(r.receita_mensal[i] for r in ganho)
        taxa_m    = sum(r.taxa_mensal[i] for r in ganho)
        result.append(FinancialMonthDTO(
            m=nome,
            bruto=round(bruto_m, 2),
            liquido=round(receita_m, 2),
            vendido=round(bruto_m, 2),
            previsto=round(bruto_m, 2),
            atual=(i == cur_idx),
        ))
    return result


def _build_produtos(ganho: list[SaleRecord]) -> list[ProductRevenueDTO]:
    totals_bruto: dict[str, float] = {}
    totals_liq: dict[str, float] = {}
    counts: dict[str, int] = {}
    for r in ganho:
        k = r.produto or "Outros"
        totals_bruto[k] = totals_bruto.get(k, 0.0) + r.bruto
        totals_liq[k]   = totals_liq.get(k, 0.0) + r.liquido_final
        counts[k]       = counts.get(k, 0) + 1

    total_bruto = sum(totals_bruto.values()) or 1.0
    return [
        ProductRevenueDTO(
            nome=nome,
            bruto=round(totals_bruto[nome], 2),
            liquido=round(totals_liq[nome], 2),
            vendas=counts[nome],
            pct=_safe_pct(totals_bruto[nome], total_bruto),
            cor=_product_color(nome),
        )
        for nome in sorted(totals_bruto, key=lambda n: totals_bruto[n], reverse=True)
    ]


def _build_canais(ganho: list[SaleRecord]) -> list[ChannelRevenueDTO]:
    totals_bruto: dict[str, float] = {}
    totals_liq: dict[str, float] = {}
    counts: dict[str, int] = {}
    for r in ganho:
        k = r.canal or "Outros"
        totals_bruto[k] = totals_bruto.get(k, 0.0) + r.bruto
        totals_liq[k]   = totals_liq.get(k, 0.0) + r.liquido_final
        counts[k]       = counts.get(k, 0) + 1

    return [
        ChannelRevenueDTO(
            id=normalize_for_compare(nome).replace(" ", "_"),
            nome=nome,
            bruto=round(totals_bruto[nome], 2),
            liquido=round(totals_liq[nome], 2),
            vendas=counts[nome],
            cor=_channel_color(nome),
        )
        for nome in sorted(totals_bruto, key=lambda n: totals_bruto[n], reverse=True)
    ]


def _build_breakdown(ganho: list[SaleRecord]) -> list[FinancialBreakdownDTO]:
    bruto     = sum(r.bruto for r in ganho)
    taxa_plat = sum(r.taxa_entrada + r.taxa_restante for r in ganho)
    imposto   = sum(r.imposto for r in ganho)
    com_sdr   = sum(r.comissao_sdr_liq for r in ganho)
    com_clos  = sum(r.comissao_closer_liq for r in ganho)
    liquido   = sum(r.liquido_final for r in ganho)

    return [
        FinancialBreakdownDTO(item="Receita Bruta",      valor=round(bruto, 2),     tipo="entrada"),
        FinancialBreakdownDTO(item="Taxa Plataforma",    valor=round(taxa_plat, 2), tipo="saida"),
        FinancialBreakdownDTO(item="Imposto",            valor=round(imposto, 2),   tipo="saida"),
        FinancialBreakdownDTO(item="Comissão SDR",       valor=round(com_sdr, 2),   tipo="saida"),
        FinancialBreakdownDTO(item="Comissão Closer",    valor=round(com_clos, 2),  tipo="saida"),
        FinancialBreakdownDTO(item="Líquido Final",      valor=round(liquido, 2),   tipo="resultado"),
    ]


def _build_tabela(ganho: list[SaleRecord]) -> MonthlyFinancialTableDTO:
    cur_idx = _current_month_idx()

    def month_sums(attr: str) -> list[float]:
        return [round(sum(getattr(r, attr)[i] for r in ganho), 2) for i in range(12)]

    bruto_m   = month_sums("bruto_mensal")
    taxa_m    = month_sums("taxa_mensal")
    sdr_m     = month_sums("sdr_mensal")
    closer_m  = month_sums("closer_mensal")
    receita_m = month_sums("receita_mensal")

    linhas = [
        MonthlyFinancialTableRowDTO(
            id="bruto",        nome="Receita Bruta",    tipo="entrada",
            valores=bruto_m,   total=round(sum(bruto_m), 2),
        ),
        MonthlyFinancialTableRowDTO(
            id="taxa",         nome="Taxa Plataforma",  tipo="saida",
            valores=taxa_m,    total=round(sum(taxa_m), 2),
        ),
        MonthlyFinancialTableRowDTO(
            id="comissao_sdr", nome="Comissão SDR",     tipo="saida",
            valores=sdr_m,     total=round(sum(sdr_m), 2),
        ),
        MonthlyFinancialTableRowDTO(
            id="comissao_closer", nome="Comissão Closer", tipo="saida",
            valores=closer_m,  total=round(sum(closer_m), 2),
        ),
        MonthlyFinancialTableRowDTO(
            id="liquido",      nome="Líquido Final",    tipo="resultado",
            valores=receita_m, total=round(sum(receita_m), 2),
        ),
    ]

    return MonthlyFinancialTableDTO(
        meses=list(MONTH_NAMES),
        mesAtualIdx=cur_idx,
        linhas=linhas,
    )


# ── public API ────────────────────────────────────────────────────────────────

def get_sales_finance_data(
    data_inicio: Optional[int] = None,
    data_fim: Optional[int] = None,
    canal: Optional[str] = None,
    produto: Optional[str] = None,
) -> SalesFinanceResponseDTO:
    try:
        matrix = read_tab(settings.default_spreadsheet_id, "BASE_VENDAS")
        records = parse_base_vendas(matrix)

        records = filter_records(
            records,
            start_ms=data_inicio,
            end_ms=data_fim,
            canal=canal,
            produto=produto,
        )

        ganho  = [r for r in records if normalize_for_compare(r.status) == "ganho"]
        em_neg = [r for r in records
                  if normalize_for_compare(r.status) not in ("ganho", "perdido")]

        produtos = _build_produtos(ganho)
        produtos_total = ProductsTotalDTO(
            bruto=round(sum(p.bruto for p in produtos), 2),
            liquido=round(sum(p.liquido for p in produtos), 2),
            vendas=sum(p.vendas for p in produtos),
        )

        return SalesFinanceResponseDTO(
            FIN_RESUMO=_build_resumo(ganho, em_neg),
            MESES_FIN=_build_meses_fin(ganho),
            PRODUTOS=produtos,
            PRODUTOS_TOTAL=produtos_total,
            RECEITA_POR_CANAL=_build_canais(ganho),
            FIN_BREAKDOWN=_build_breakdown(ganho),
            TABELA_FIN_MENSAL=_build_tabela(ganho),
        )

    except Exception as exc:
        logger.warning("finance_service: error building response | type={} | detail={}",
                       type(exc).__name__, str(exc))
        return SalesFinanceResponseDTO()
