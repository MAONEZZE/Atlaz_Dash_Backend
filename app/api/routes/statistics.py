from typing import Optional

from fastapi import APIRouter, Query
from loguru import logger

from app.dtos.statistics_dto import StatisticResponseDTO
from app.mappers.statistics_mapper import map_to_statistic_response
from app.services.statistics_service import get_statistics

router = APIRouter()


@router.get("/statistics", response_model=None)
async def statistics(
    data_inicio: Optional[int] = Query(default=None, description="Início do período (timestamp ms)"),
    data_fim: Optional[int] = Query(default=None, description="Fim do período (timestamp ms)"),
    responsavel: Optional[int] = Query(default=None, description="ID do usuário (dash_users.id)"),
    produto: Optional[str] = Query(default=None),
    etapa_do_funil: Optional[str] = Query(default=None),
    status_do_negocio: Optional[str] = Query(default=None),
    tipo_de_receita: Optional[str] = Query(default=None),
    faixa_de_ticket: Optional[str] = Query(default=None),
    tipo_de_atividade: Optional[str] = Query(default=None),
) -> dict:
    """
    Estatísticas consolidadas (Visão Geral) — Closer e SDR.
    Mês atual: busca no n8n. Meses passados: busca no Supabase.
    Todos os filtros são opcionais e acumulativos.
    """
    try:
        stats = await get_statistics(
            start_ms=data_inicio,
            end_ms=data_fim,
            user_id=responsavel,
            produto=produto,
            etapa_do_funil=etapa_do_funil,
            status_do_negocio=status_do_negocio,
            tipo_de_receita=tipo_de_receita,
            faixa_de_ticket=faixa_de_ticket,
            tipo_de_atividade=tipo_de_atividade,
        )
        response = map_to_statistic_response(stats)
    except Exception as exc:
        logger.warning("statistics route: unexpected error | type={} | detail={}", type(exc).__name__, str(exc))
        response = StatisticResponseDTO.empty()

    return response.model_dump()
