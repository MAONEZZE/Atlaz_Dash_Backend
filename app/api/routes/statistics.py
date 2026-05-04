from fastapi import APIRouter
from loguru import logger

from app.dtos.statistics_dto import StatisticResponseDTO
from app.mappers.statistics_mapper import map_to_statistic_response
from app.schemas.filters_schema import StatisticsFilter
from app.services.statistics_service import get_statistics

router = APIRouter()


@router.post("/statistics", response_model=None)
async def statistics(filters: StatisticsFilter = StatisticsFilter()) -> dict:
    """
    Return consolidated statistics (Visão Geral) for Closer and SDR teams.
    Current month data sourced from n8n; past months from Supabase.
    Filters are optional and accumulative.
    """
    try:
        stats = await get_statistics(
            start_ms=filters.start_date,
            end_ms=filters.end_date,
            channel=filters.channel,
            responsible=filters.responsible,
            product=filters.product,
            stage=filters.stage,
            status=filters.status,
            revenue_type=filters.revenue_type,
            ticket_range=filters.ticket_range,
            activity=filters.activity,
        )
        response = map_to_statistic_response(stats)
    except Exception as exc:
        logger.warning("statistics route: unexpected error | type={} | detail={}", type(exc).__name__, str(exc))
        response = StatisticResponseDTO.empty()

    return response.model_dump()
