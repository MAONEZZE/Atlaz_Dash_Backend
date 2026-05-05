"""
Pre-sales funnel DTOs — Phase 2 placeholder.
All channels always present; zeroed when no data.
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional


FunnelFmt = Literal["num", "pct", "dec", "h", "dias"]


class FunnelStepDTO(BaseModel):
    id: str = ""
    nome: str = ""
    v: int = 0


class FunnelKpiDTO(BaseModel):
    id: str = ""
    l: str = ""
    meta: int = 0
    auxRef: Optional[str] = None


class FunnelAuxBlockDTO(BaseModel):
    l: str = ""
    v: float = 0
    fmt: FunnelFmt = "num"


class FunnelAuxDTO(BaseModel):
    titulo: str = ""
    blocos: list[FunnelAuxBlockDTO] = Field(default_factory=list)


class ChannelFunnelDTO(BaseModel):
    id: str = ""
    nome: str = ""
    cor: str = "#6B7280"
    corAcc: str = "#4B5563"
    sub: str = ""
    etapas: list[FunnelStepDTO] = Field(default_factory=list)
    kpis: list[FunnelKpiDTO] = Field(default_factory=list)
    aux: FunnelAuxDTO = Field(default_factory=FunnelAuxDTO)


class PreSalesFunnelDTO(BaseModel):
    linkedin: ChannelFunnelDTO = Field(default_factory=lambda: ChannelFunnelDTO(
        id="linkedin", nome="LinkedIn", cor="#0077B5", corAcc="#005885", sub="Prospecção via LinkedIn"
    ))
    instagram: ChannelFunnelDTO = Field(default_factory=lambda: ChannelFunnelDTO(
        id="instagram", nome="Instagram", cor="#E1306C", corAcc="#B02356", sub="Prospecção via Instagram"
    ))
    indicacao: ChannelFunnelDTO = Field(default_factory=lambda: ChannelFunnelDTO(
        id="indicacao", nome="Indicação", cor="#F59E0B", corAcc="#D97706", sub="Leads por indicação"
    ))
    whatsapp: ChannelFunnelDTO = Field(default_factory=lambda: ChannelFunnelDTO(
        id="whatsapp", nome="WhatsApp", cor="#25D366", corAcc="#1DA850", sub="Prospecção via WhatsApp"
    ))
    outros: ChannelFunnelDTO = Field(default_factory=lambda: ChannelFunnelDTO(
        id="outros", nome="Outros", cor="#6B7280", corAcc="#4B5563", sub="Outros canais"
    ))


class PreSalesResponseDTO(BaseModel):
    FUNIS_POR_CANAL: PreSalesFunnelDTO = Field(default_factory=PreSalesFunnelDTO)
