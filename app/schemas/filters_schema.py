from typing import Optional
from pydantic import BaseModel


class StatisticsFilter(BaseModel):
    """Filter parameters for /statistics. All fields optional."""
    data_inicio: Optional[int] = None       # timestamp ms
    data_fim: Optional[int] = None          # timestamp ms
    responsavel: Optional[int] = None       # dash_users.id (bigint)
    produto: Optional[str] = None           # KeepSide | Produto de Aceleração | ...
    etapa_do_funil: Optional[str] = None    # Prospecção | Qualificação | Reunião | Proposta | Fechamento
    status_do_negocio: Optional[str] = None # Em negociação | Ganho | Perdido | Cancelado
    tipo_de_receita: Optional[str] = None   # bruto | liquido | parcelado
    faixa_de_ticket: Optional[str] = None   # Baixo | Médio | Alto
    tipo_de_atividade: Optional[str] = None # Ligação | Reunião | Indicação | Números Captados


class DateRangeFilter(BaseModel):
    """Minimal date range for finance and funnel endpoints."""
    data_inicio: Optional[int] = None  # timestamp ms
    data_fim: Optional[int] = None     # timestamp ms
