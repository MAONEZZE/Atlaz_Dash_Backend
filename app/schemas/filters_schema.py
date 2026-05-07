from typing import Literal, Optional
from pydantic import BaseModel


Canal = Literal["linkedin", "instagram", "indicacao", "whatsapp", "outros"]
Responsavel = str  # "closers" | "sdrs" | int string (user id)
Produto = Literal["keepside", "aceleracao", "ativacao", "entrada", "boltique"]
EtapaFunil = Literal["prospeccao", "qualificacao", "reuniao", "proposta", "fechamento"]
StatusNegocio = Literal["em-negociacao", "ganho", "perdido", "cancelado"]
TipoReceita = Literal["bruta", "liquida", "parcelada", "recorrente"]
FaixaTicket = Literal["baixo", "medio", "alto"]
TipoAtividade = Literal["ligacoes", "reunioes", "indicacoes", "numeros"]


class DashboardFilters(BaseModel):
    """Query params shared by /metrics and /users/{id}/metrics."""
    data_inicio: Optional[int] = None
    data_fim:    Optional[int] = None
    responsavel: Optional[str] = None
    canal:             Optional[Canal]         = None
    produto:           Optional[Produto]       = None
    etapa_do_funil:    Optional[EtapaFunil]    = None
    status_do_negocio: Optional[StatusNegocio] = None
    tipo_de_receita:   Optional[TipoReceita]   = None
    faixa_de_ticket:   Optional[FaixaTicket]   = None
    tipo_de_atividade: Optional[TipoAtividade] = None


class SalesFilters(BaseModel):
    """Query params for /sales/values."""
    data_inicio: Optional[int] = None
    data_fim:    Optional[int] = None
    canal:   Optional[Canal]   = None
    produto: Optional[Produto] = None


class FunnelFilters(BaseModel):
    """Query params for /pre-sales/funnels."""
    data_inicio: Optional[int] = None
    data_fim:    Optional[int] = None
