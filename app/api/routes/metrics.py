from typing import Annotated

from fastapi import APIRouter, Depends
from loguru import logger

from app.core.auth import require_auth
from app.dtos.statistics_dto import StatisticResponseDTO
from app.mappers.statistics_mapper import map_to_statistic_response
from app.schemas.filters_schema import DashboardFilters
from app.services.statistics_service import get_statistics

router = APIRouter()


@router.get("/metrics", response_model=None, dependencies=[Depends(require_auth)])
async def metrics(
    filters: Annotated[DashboardFilters, Depends()],
) -> dict:
    """
    Estatísticas consolidadas (Visão Geral) — Closer e SDR.
    Mês atual: busca no n8n. Meses passados: busca no Supabase.
    Todos os filtros são opcionais e acumulativos.
    """
    try:
        stats = await get_statistics(
            start_ms=filters.data_inicio,
            end_ms=filters.data_fim,
            responsavel=filters.responsavel,
            canal=filters.canal,
            produto=filters.produto,
            etapa_do_funil=filters.etapa_do_funil,
            status_do_negocio=filters.status_do_negocio,
            tipo_de_receita=filters.tipo_de_receita,
            faixa_de_ticket=filters.faixa_de_ticket,
            tipo_de_atividade=filters.tipo_de_atividade,
        )
        response = map_to_statistic_response(stats)
    except Exception as exc:
        logger.warning("metrics route: unexpected error | type={} | detail={}", type(exc).__name__, str(exc))
        response = StatisticResponseDTO.empty()

    return response.model_dump()
