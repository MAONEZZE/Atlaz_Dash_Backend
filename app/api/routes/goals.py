import httpx
from fastapi import APIRouter
from loguru import logger

from app.core.config import settings
from app.dtos.goals_dto import GoalsResponseDTO
from app.mappers.goals_mapper import map_to_goals_response
from app.repositories.goals_repository import fetch_goals_raw
from app.services.goals_service import parse_goals

router = APIRouter()


@router.get("/goals/fat", response_model=None)
async def get_goals_fat() -> dict:
    """Return individual goals from METAS sheet tab (Planilha Isaac Newton)."""
    try:
        matrix = fetch_goals_raw()
        goals = parse_goals(matrix)
        return map_to_goals_response(goals).model_dump()
    except Exception as exc:
        logger.warning("goals/fat route: error | type={} | detail={}", type(exc).__name__, str(exc))
        return GoalsResponseDTO(data=[]).model_dump()


@router.get("/goals/metrics", response_model=None)
async def get_goals_metrics() -> dict:
    """Return daily team goal totals from n8n (SDR + Closer)."""
    url = settings.n8n_team_goals_url
    timeout = float(settings.n8n_statistics_timeout_seconds)
    empty = {"SDR": {}, "Closer": {}}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
        if not isinstance(data, dict):
            logger.warning("goals/metrics: unexpected shape | type={}", type(data))
            return empty
        return data
    except httpx.TimeoutException:
        logger.warning("goals/metrics: timeout | url={}", url)
        return empty
    except httpx.HTTPStatusError as exc:
        logger.warning("goals/metrics: HTTP {} | url={}", exc.response.status_code, url)
        return empty
    except Exception as exc:
        logger.warning("goals/metrics: error | type={} | detail={}", type(exc).__name__, str(exc))
        return empty
