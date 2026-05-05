"""
Pre-sales service.
- Activity metrics (top-of-funnel) per channel: fetched from n8n with canal filter.
- Closings (fechamentos) per channel: read from BASE_VENDAS.
"""

import asyncio
from typing import Optional

from loguru import logger

from app.core.config import settings
from app.dtos.pre_sales_dto import (
    ChannelFunnelDTO,
    FunnelAuxBlockDTO,
    FunnelAuxDTO,
    FunnelKpiDTO,
    FunnelStepDTO,
    PreSalesFunnelDTO,
    PreSalesResponseDTO,
)
from app.services.base_vendas_parser import filter_records, parse_base_vendas
from app.services.google_sheets_service import read_tab
from app.services.n8n_statistics_client import fetch_current_month_statistics
from app.utils.normalize_number import normalize_number

# Canonical canal names sent to n8n as filter
_CANAL_N8N_LABEL = {
    "linkedin":  "LinkedIn",
    "instagram": "Instagram",
    "indicacao": "Indicação",
    "whatsapp":  "WhatsApp",
    "outros":    "Outros",
}

# Canal → event canal label in BASE_VENDAS
_CANAL_BV_LABEL = {
    "linkedin":  "LinkedIn",
    "instagram": "Instagram",
    "indicacao": "Indicação",
    "whatsapp":  "WhatsApp",
    "outros":    "Outros",
}


def _sum_sdr(raw_list: list[dict], field: str) -> int:
    return int(sum(normalize_number(r.get(field, 0)) for r in raw_list))


def _build_linkedin(sdr: list, closer: list, fechamentos: int) -> ChannelFunnelDTO:
    enviadas   = _sum_sdr(sdr, "Conexoes_Enviadas")
    aceitas    = _sum_sdr(sdr, "Conexoes_Aceitas")
    abordagens = _sum_sdr(sdr, "Abordagens")
    followups  = _sum_sdr(sdr, "Follow_ups")
    numeros    = _sum_sdr(sdr, "Numeros_Captados")
    lig_ag     = _sum_sdr(sdr, "Ligacoes_Agendadas")
    ind_cap    = _sum_sdr(sdr, "Indicacoes_Captadas")
    lig_real   = int(sum(normalize_number(r.get("Ligacoes_Realizadas", 0)) for r in closer))
    reu_ag     = int(sum(normalize_number(r.get("Reunioes_Agendadas",  0)) for r in closer))
    reu_real   = int(sum(normalize_number(r.get("Reunioes_Realizadas", 0)) for r in closer))

    return ChannelFunnelDTO(
        id="linkedin", nome="LinkedIn", cor="#0077B5", corAcc="#005885",
        sub="Prospecção outbound estruturada via conexão direta",
        etapas=[
            FunnelStepDTO(id="enviadas",    nome="Conexões enviadas",   v=enviadas),
            FunnelStepDTO(id="aceitas",     nome="Conexões aceitas",    v=aceitas),
            FunnelStepDTO(id="abordagens",  nome="Abordagens feitas",   v=abordagens),
            FunnelStepDTO(id="numeros",     nome="Números captados",    v=numeros),
            FunnelStepDTO(id="ligAgend",    nome="Ligações agendadas",  v=lig_ag),
            FunnelStepDTO(id="ligReal",     nome="Ligações realizadas", v=lig_real),
            FunnelStepDTO(id="reuAgend",    nome="Reuniões agendadas",  v=reu_ag),
            FunnelStepDTO(id="reuReal",     nome="Reuniões realizadas", v=reu_real),
            FunnelStepDTO(id="fechamentos", nome="Fechamentos",         v=fechamentos),
        ],
        kpis=[
            FunnelKpiDTO(id="enviadas",    l="Conexões enviadas",  meta=0),
            FunnelKpiDTO(id="aceitas",     l="Conexões aceitas",   meta=0),
            FunnelKpiDTO(id="abordagens",  l="Abordagens feitas",  meta=0),
            FunnelKpiDTO(id="followups",   l="Follow-ups feitos",  meta=0, auxRef="followups"),
            FunnelKpiDTO(id="numeros",     l="Números captados",   meta=0),
            FunnelKpiDTO(id="ligAgend",    l="Ligações agendadas", meta=0),
            FunnelKpiDTO(id="reuAgend",    l="Reuniões agendadas", meta=0),
            FunnelKpiDTO(id="fechamentos", l="Fechamentos",        meta=0),
        ],
        aux=FunnelAuxDTO(
            titulo="Follow-up & engajamento",
            blocos=[
                FunnelAuxBlockDTO(l="Follow-ups feitos",  v=followups, fmt="num"),
                FunnelAuxBlockDTO(l="InMails enviados",   v=_sum_sdr(sdr, "InMails_Enviados"), fmt="num"),
                FunnelAuxBlockDTO(l="Indicações captadas", v=ind_cap, fmt="num"),
            ],
        ),
    )


def _build_instagram(sdr: list, closer: list, fechamentos: int) -> ChannelFunnelDTO:
    numeros  = _sum_sdr(sdr, "Numeros_Captados")
    lig_ag   = _sum_sdr(sdr, "Ligacoes_Agendadas")
    lig_real = int(sum(normalize_number(r.get("Ligacoes_Realizadas", 0)) for r in closer))
    reu_ag   = int(sum(normalize_number(r.get("Reunioes_Agendadas",  0)) for r in closer))
    reu_real = int(sum(normalize_number(r.get("Reunioes_Realizadas", 0)) for r in closer))
    abord    = _sum_sdr(sdr, "Abordagens")
    followup = _sum_sdr(sdr, "Follow_ups")

    return ChannelFunnelDTO(
        id="instagram", nome="Instagram", cor="#E1306C", corAcc="#B02356",
        sub="Abordagem via DM + conteúdo orgânico",
        etapas=[
            FunnelStepDTO(id="abordagens", nome="Mensagens enviadas",  v=abord),
            FunnelStepDTO(id="numeros",    nome="Números captados",    v=numeros),
            FunnelStepDTO(id="ligAgend",   nome="Ligações agendadas",  v=lig_ag),
            FunnelStepDTO(id="ligReal",    nome="Ligações realizadas", v=lig_real),
            FunnelStepDTO(id="reuAgend",   nome="Reuniões agendadas",  v=reu_ag),
            FunnelStepDTO(id="reuReal",    nome="Reuniões realizadas", v=reu_real),
            FunnelStepDTO(id="fechamentos",nome="Fechamentos",         v=fechamentos),
        ],
        kpis=[
            FunnelKpiDTO(id="abordagens",  l="Mensagens enviadas",  meta=0),
            FunnelKpiDTO(id="numeros",     l="Números captados",    meta=0),
            FunnelKpiDTO(id="ligAgend",    l="Ligações agendadas",  meta=0),
            FunnelKpiDTO(id="reuAgend",    l="Reuniões agendadas",  meta=0),
            FunnelKpiDTO(id="fechamentos", l="Fechamentos",         meta=0),
        ],
        aux=FunnelAuxDTO(
            titulo="Engajamento & follow-up",
            blocos=[
                FunnelAuxBlockDTO(l="Follow-ups feitos", v=followup, fmt="num"),
            ],
        ),
    )


def _build_indicacao(sdr: list, closer: list, fechamentos: int) -> ChannelFunnelDTO:
    ind_cap  = _sum_sdr(sdr, "Indicacoes_Captadas")
    numeros  = _sum_sdr(sdr, "Numeros_Captados")
    lig_ag   = _sum_sdr(sdr, "Ligacoes_Agendadas")
    lig_real = int(sum(normalize_number(r.get("Ligacoes_Realizadas", 0)) for r in closer))
    reu_ag   = int(sum(normalize_number(r.get("Reunioes_Agendadas",  0)) for r in closer))
    reu_real = int(sum(normalize_number(r.get("Reunioes_Realizadas", 0)) for r in closer))

    return ChannelFunnelDTO(
        id="indicacao", nome="Indicação", cor="#F59E0B", corAcc="#D97706",
        sub="Canal de maior confiança e velocidade de fechamento",
        etapas=[
            FunnelStepDTO(id="indicacoes", nome="Indicações recebidas",  v=ind_cap),
            FunnelStepDTO(id="numeros",    nome="Números captados",      v=numeros),
            FunnelStepDTO(id="ligAgend",   nome="Ligações agendadas",    v=lig_ag),
            FunnelStepDTO(id="ligReal",    nome="Ligações realizadas",   v=lig_real),
            FunnelStepDTO(id="reuAgend",   nome="Reuniões agendadas",    v=reu_ag),
            FunnelStepDTO(id="reuReal",    nome="Reuniões realizadas",   v=reu_real),
            FunnelStepDTO(id="fechamentos",nome="Fechamentos",           v=fechamentos),
        ],
        kpis=[
            FunnelKpiDTO(id="indicacoes",  l="Indicações recebidas", meta=0),
            FunnelKpiDTO(id="numeros",     l="Números captados",     meta=0),
            FunnelKpiDTO(id="ligAgend",    l="Ligações agendadas",   meta=0),
            FunnelKpiDTO(id="reuAgend",    l="Reuniões agendadas",   meta=0),
            FunnelKpiDTO(id="fechamentos", l="Fechamentos",          meta=0),
        ],
        aux=FunnelAuxDTO(titulo="Indicações", blocos=[
            FunnelAuxBlockDTO(l="Indicações captadas", v=ind_cap, fmt="num"),
        ]),
    )


def _build_whatsapp(sdr: list, closer: list, fechamentos: int) -> ChannelFunnelDTO:
    abord    = _sum_sdr(sdr, "Abordagens")
    numeros  = _sum_sdr(sdr, "Numeros_Captados")
    lig_ag   = _sum_sdr(sdr, "Ligacoes_Agendadas")
    lig_real = int(sum(normalize_number(r.get("Ligacoes_Realizadas", 0)) for r in closer))
    reu_ag   = int(sum(normalize_number(r.get("Reunioes_Agendadas",  0)) for r in closer))
    reu_real = int(sum(normalize_number(r.get("Reunioes_Realizadas", 0)) for r in closer))

    return ChannelFunnelDTO(
        id="whatsapp", nome="WhatsApp", cor="#25D366", corAcc="#1DA850",
        sub="Prospecção e qualificação via WhatsApp",
        etapas=[
            FunnelStepDTO(id="abordagens", nome="Abordagens feitas",   v=abord),
            FunnelStepDTO(id="numeros",    nome="Números captados",    v=numeros),
            FunnelStepDTO(id="ligAgend",   nome="Ligações agendadas",  v=lig_ag),
            FunnelStepDTO(id="ligReal",    nome="Ligações realizadas", v=lig_real),
            FunnelStepDTO(id="reuAgend",   nome="Reuniões agendadas",  v=reu_ag),
            FunnelStepDTO(id="reuReal",    nome="Reuniões realizadas", v=reu_real),
            FunnelStepDTO(id="fechamentos",nome="Fechamentos",         v=fechamentos),
        ],
        kpis=[
            FunnelKpiDTO(id="abordagens",  l="Abordagens feitas",   meta=0),
            FunnelKpiDTO(id="numeros",     l="Números captados",    meta=0),
            FunnelKpiDTO(id="ligAgend",    l="Ligações agendadas",  meta=0),
            FunnelKpiDTO(id="reuAgend",    l="Reuniões agendadas",  meta=0),
            FunnelKpiDTO(id="fechamentos", l="Fechamentos",         meta=0),
        ],
        aux=FunnelAuxDTO(titulo="Atividade", blocos=[]),
    )


def _build_outros(sdr: list, closer: list, fechamentos: int) -> ChannelFunnelDTO:
    abord    = _sum_sdr(sdr, "Abordagens")
    numeros  = _sum_sdr(sdr, "Numeros_Captados")
    lig_ag   = _sum_sdr(sdr, "Ligacoes_Agendadas")
    reu_ag   = int(sum(normalize_number(r.get("Reunioes_Agendadas", 0)) for r in closer))
    reu_real = int(sum(normalize_number(r.get("Reunioes_Realizadas", 0)) for r in closer))

    return ChannelFunnelDTO(
        id="outros", nome="Outros", cor="#6B7280", corAcc="#4B5563",
        sub="Outros canais de aquisição",
        etapas=[
            FunnelStepDTO(id="abordagens", nome="Abordagens feitas",   v=abord),
            FunnelStepDTO(id="numeros",    nome="Números captados",    v=numeros),
            FunnelStepDTO(id="ligAgend",   nome="Ligações agendadas",  v=lig_ag),
            FunnelStepDTO(id="reuAgend",   nome="Reuniões agendadas",  v=reu_ag),
            FunnelStepDTO(id="reuReal",    nome="Reuniões realizadas", v=reu_real),
            FunnelStepDTO(id="fechamentos",nome="Fechamentos",         v=fechamentos),
        ],
        kpis=[
            FunnelKpiDTO(id="abordagens",  l="Abordagens feitas",   meta=0),
            FunnelKpiDTO(id="numeros",     l="Números captados",    meta=0),
            FunnelKpiDTO(id="ligAgend",    l="Ligações agendadas",  meta=0),
            FunnelKpiDTO(id="reuAgend",    l="Reuniões agendadas",  meta=0),
            FunnelKpiDTO(id="fechamentos", l="Fechamentos",         meta=0),
        ],
        aux=FunnelAuxDTO(titulo="Atividade", blocos=[]),
    )


_CANAL_BUILDERS = {
    "linkedin":  _build_linkedin,
    "instagram": _build_instagram,
    "indicacao": _build_indicacao,
    "whatsapp":  _build_whatsapp,
    "outros":    _build_outros,
}


async def get_pre_sales_funnels(
    data_inicio: Optional[int] = None,
    data_fim: Optional[int] = None,
) -> PreSalesResponseDTO:
    try:
        # Fetch n8n stats for each canal in parallel
        canal_keys = list(_CANAL_N8N_LABEL.keys())
        n8n_tasks = [
            fetch_current_month_statistics(
                data_inicio=data_inicio,
                data_fim=data_fim,
                canal=_CANAL_N8N_LABEL[k],
            )
            for k in canal_keys
        ]
        n8n_results = await asyncio.gather(*n8n_tasks, return_exceptions=True)
        n8n_by_canal: dict[str, dict] = {}
        for i, k in enumerate(canal_keys):
            r = n8n_results[i]
            if isinstance(r, Exception):
                logger.warning("pre_sales: n8n fetch failed for canal={} | {}", k, r)
                n8n_by_canal[k] = {"SDR": [], "CLOSER": []}
            else:
                n8n_by_canal[k] = r if isinstance(r, dict) else {"SDR": [], "CLOSER": []}

        # Fechamentos per canal from BASE_VENDAS
        fechamentos_by_canal: dict[str, int] = {k: 0 for k in canal_keys}
        try:
            matrix = read_tab(settings.default_spreadsheet_id, "BASE_VENDAS")
            records = parse_base_vendas(matrix)
            filtered = filter_records(records, start_ms=data_inicio, end_ms=data_fim, status="Ganho")
            for r in filtered:
                from app.utils.normalize_text import normalize_for_compare
                canal_raw = normalize_for_compare(r.canal)
                # map canal raw to key
                for k, label in _CANAL_BV_LABEL.items():
                    if normalize_for_compare(label) == canal_raw:
                        fechamentos_by_canal[k] += 1
                        break
        except Exception as exc:
            logger.warning("pre_sales: BASE_VENDAS read failed | {}", exc)

        # Build each canal
        built: dict[str, ChannelFunnelDTO] = {}
        for k in canal_keys:
            raw = n8n_by_canal[k]
            sdr    = raw.get("SDR", [])
            closer = raw.get("CLOSER", [])
            fech   = fechamentos_by_canal[k]
            try:
                built[k] = _CANAL_BUILDERS[k](sdr, closer, fech)
            except Exception as exc:
                logger.warning("pre_sales: build failed for canal={} | {}", k, exc)

        return PreSalesResponseDTO(
            FUNIS_POR_CANAL=PreSalesFunnelDTO(
                linkedin  = built.get("linkedin",  ChannelFunnelDTO(id="linkedin",  nome="LinkedIn")),
                instagram = built.get("instagram", ChannelFunnelDTO(id="instagram", nome="Instagram")),
                indicacao = built.get("indicacao", ChannelFunnelDTO(id="indicacao", nome="Indicação")),
                whatsapp  = built.get("whatsapp",  ChannelFunnelDTO(id="whatsapp",  nome="WhatsApp")),
                outros    = built.get("outros",    ChannelFunnelDTO(id="outros",    nome="Outros")),
            )
        )

    except Exception as exc:
        logger.warning("pre_sales_service: unexpected error | type={} | detail={}", type(exc).__name__, str(exc))
        return PreSalesResponseDTO()
