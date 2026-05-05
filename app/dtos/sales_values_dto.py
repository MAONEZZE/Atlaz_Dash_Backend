"""Sales finance DTOs. Data source: BASE_VENDAS tab."""
from pydantic import BaseModel, Field
from typing import Literal


class FinancialSummaryDTO(BaseModel):
    bruto: float = 0
    liquido: float = 0
    vendido: float = 0
    vendas: int = 0
    deltaLiquido: float = 0
    deltaBruto: float = 0
    deltaVendas: float = 0
    margem: float = 0
    deltaMargem: float = 0
    taxaPlataforma: float = 0
    ticketMedio: float = 0
    emNegociacaoValor: float = 0
    emNegociacaoQtd: int = 0
    comissaoSDR: float = 0
    comissaoCloser: float = 0
    comissaoTotal: float = 0
    margemOpValor: float = 0


class FinancialMonthDTO(BaseModel):
    m: str = ""
    bruto: float = 0
    liquido: float = 0
    vendido: float = 0
    previsto: float = 0
    atual: bool = False


class ProductRevenueDTO(BaseModel):
    nome: str = ""
    bruto: float = 0
    liquido: float = 0
    vendas: int = 0
    pct: float = 0
    cor: str = "#6B7280"


class ChannelRevenueDTO(BaseModel):
    id: str = ""
    nome: str = ""
    bruto: float = 0
    liquido: float = 0
    vendas: int = 0
    cor: str = "#6B7280"


class FinancialBreakdownDTO(BaseModel):
    item: str = ""
    valor: float = 0
    tipo: Literal["entrada", "saida", "resultado"] = "entrada"


class MonthlyFinancialTableRowDTO(BaseModel):
    id: str = ""
    nome: str = ""
    tipo: Literal["entrada", "saida", "subtotal", "resultado"] = "entrada"
    valores: list[float] = Field(default_factory=list)
    total: float = 0


class MonthlyFinancialTableDTO(BaseModel):
    meses: list[str] = Field(default_factory=lambda: [
        "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
        "Jul", "Ago", "Set", "Out", "Nov", "Dez",
    ])
    mesAtualIdx: int = 0
    linhas: list[MonthlyFinancialTableRowDTO] = Field(default_factory=list)


class ProductsTotalDTO(BaseModel):
    bruto: float = 0
    liquido: float = 0
    vendas: int = 0


class SalesFinanceResponseDTO(BaseModel):
    FIN_RESUMO: FinancialSummaryDTO = Field(default_factory=FinancialSummaryDTO)
    MESES_FIN: list[FinancialMonthDTO] = Field(default_factory=list)
    PRODUTOS: list[ProductRevenueDTO] = Field(default_factory=list)
    PRODUTOS_TOTAL: ProductsTotalDTO = Field(default_factory=ProductsTotalDTO)
    RECEITA_POR_CANAL: list[ChannelRevenueDTO] = Field(default_factory=list)
    FIN_BREAKDOWN: list[FinancialBreakdownDTO] = Field(default_factory=list)
    TABELA_FIN_MENSAL: MonthlyFinancialTableDTO = Field(default_factory=MonthlyFinancialTableDTO)
