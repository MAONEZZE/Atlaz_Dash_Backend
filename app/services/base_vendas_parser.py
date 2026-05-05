"""
Parser for the BASE_VENDAS Google Sheets tab.

Column layout (row index 2 = headers, data starts at row index 3):
  0   ID
  1   Data da Venda (DD/MM/YYYY)
  2   Nome do Cliente
  8   Produto
  9   Valor Bruto (R$)
  10  Canal de Origem
  17  Status da Venda
  18  SDR
  19  Closer
  20  Valor Entrada (R$)
  24  Valor Restante (R$)
  31  R$ Taxa Entrada
  37  R$ Taxa Restante
  43  R$ Imposto
  44  Total Deduções
  45  Líq Final no Caixa
  46  Com. SDR s/ Bruto
  47  Com. SDR s/ Líq Final
  48  Com. Closer s/ Bruto
  49  Com. Closer s/ Líq Final
  51-62   Receita mensal prevista Jan-Dez (net after platform fees)
  63-74   Taxa plataforma mensal Jan-Dez
  75-86   Comissão SDR mensal Jan-Dez
  87-98   Comissão Closer mensal Jan-Dez
  99-110  Bruto mensal Jan-Dez
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.utils.normalize_currency import normalize_currency
from app.utils.normalize_date import normalize_date
from app.utils.normalize_text import normalize_for_compare

MONTH_NAMES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
               "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

# Column offsets for monthly data blocks (12 months each)
_COL_RECEITA_BASE = 51   # net revenue per month
_COL_TAXA_BASE    = 63   # platform fee per month
_COL_SDR_BASE     = 75   # SDR commission per month
_COL_CLOSER_BASE  = 87   # Closer commission per month
_COL_BRUTO_BASE   = 99   # gross revenue per month


@dataclass
class SaleRecord:
    id: str = ""
    data_venda: Optional[datetime] = None
    cliente: str = ""
    produto: str = ""
    bruto: float = 0.0
    canal: str = ""
    status: str = ""
    sdr: str = ""
    closer: str = ""
    valor_entrada: float = 0.0
    valor_restante: float = 0.0
    taxa_entrada: float = 0.0
    taxa_restante: float = 0.0
    imposto: float = 0.0
    total_deducoes: float = 0.0
    liquido_final: float = 0.0
    comissao_sdr_bruto: float = 0.0
    comissao_sdr_liq: float = 0.0
    comissao_closer_bruto: float = 0.0
    comissao_closer_liq: float = 0.0
    # Monthly spread arrays (index 0=Jan … 11=Dez)
    receita_mensal: list[float] = field(default_factory=lambda: [0.0] * 12)
    taxa_mensal: list[float] = field(default_factory=lambda: [0.0] * 12)
    sdr_mensal: list[float] = field(default_factory=lambda: [0.0] * 12)
    closer_mensal: list[float] = field(default_factory=lambda: [0.0] * 12)
    bruto_mensal: list[float] = field(default_factory=lambda: [0.0] * 12)


def _g(row: list, idx: int) -> str:
    return str(row[idx]).strip() if idx < len(row) else ""


def _currency(row: list, idx: int) -> float:
    return normalize_currency(_g(row, idx))


def _monthly_block(row: list, base_col: int) -> list[float]:
    return [normalize_currency(_g(row, base_col + i)) for i in range(12)]


def parse_base_vendas(matrix: list[list]) -> list[SaleRecord]:
    """Parse raw BASE_VENDAS matrix. Headers on row 2, data from row 3 onward."""
    if len(matrix) < 4:
        return []

    records: list[SaleRecord] = []
    for raw_row in matrix[3:]:
        row_id = _g(raw_row, 0)
        if not row_id or not row_id.isdigit():
            continue

        status_raw = _g(raw_row, 17)
        if not status_raw:
            continue

        rec = SaleRecord(
            id=row_id,
            data_venda=normalize_date(_g(raw_row, 1)),
            cliente=_g(raw_row, 2),
            produto=_g(raw_row, 8),
            bruto=_currency(raw_row, 9),
            canal=_g(raw_row, 10),
            status=status_raw,
            sdr=_g(raw_row, 18),
            closer=_g(raw_row, 19),
            valor_entrada=_currency(raw_row, 20),
            valor_restante=_currency(raw_row, 24),
            taxa_entrada=_currency(raw_row, 31),
            taxa_restante=_currency(raw_row, 37),
            imposto=_currency(raw_row, 43),
            total_deducoes=_currency(raw_row, 44),
            liquido_final=_currency(raw_row, 45),
            comissao_sdr_bruto=_currency(raw_row, 46),
            comissao_sdr_liq=_currency(raw_row, 47),
            comissao_closer_bruto=_currency(raw_row, 48),
            comissao_closer_liq=_currency(raw_row, 49),
            receita_mensal=_monthly_block(raw_row, _COL_RECEITA_BASE),
            taxa_mensal=_monthly_block(raw_row, _COL_TAXA_BASE),
            sdr_mensal=_monthly_block(raw_row, _COL_SDR_BASE),
            closer_mensal=_monthly_block(raw_row, _COL_CLOSER_BASE),
            bruto_mensal=_monthly_block(raw_row, _COL_BRUTO_BASE),
        )
        records.append(rec)

    return records


def filter_records(
    records: list[SaleRecord],
    start_ms: Optional[int] = None,
    end_ms: Optional[int] = None,
    canal: Optional[str] = None,
    produto: Optional[str] = None,
    status: Optional[str] = None,
    closer: Optional[str] = None,
    sdr: Optional[str] = None,
) -> list[SaleRecord]:
    out = records
    if start_ms is not None:
        start_dt = datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc)
        out = [r for r in out if r.data_venda and r.data_venda >= start_dt]
    if end_ms is not None:
        end_dt = datetime.fromtimestamp(end_ms / 1000, tz=timezone.utc)
        out = [r for r in out if r.data_venda and r.data_venda <= end_dt]
    if canal:
        nc = normalize_for_compare(canal)
        out = [r for r in out if normalize_for_compare(r.canal) == nc]
    if produto:
        np = normalize_for_compare(produto)
        out = [r for r in out if normalize_for_compare(r.produto) == np]
    if status:
        ns = normalize_for_compare(status)
        out = [r for r in out if normalize_for_compare(r.status) == ns]
    if closer:
        nc2 = normalize_for_compare(closer)
        out = [r for r in out if normalize_for_compare(r.closer) == nc2]
    if sdr:
        ns2 = normalize_for_compare(sdr)
        out = [r for r in out if normalize_for_compare(r.sdr) == ns2]
    return out
