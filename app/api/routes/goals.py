from fastapi import APIRouter
from loguru import logger

from app.dtos.goals_dto import GoalsResponseDTO
from app.mappers.goals_mapper import map_to_goals_response
from app.repositories.goals_repository import fetch_goals_raw
from app.services.goals_service import parse_goals

router = APIRouter()


@router.get("/goals", response_model=None)
async def get_goals() -> dict:
    """Return individual goals from METAS sheet tab."""
    try:
        matrix = fetch_goals_raw()
        goals = parse_goals(matrix)
        return map_to_goals_response(goals).model_dump()
    except Exception as exc:
        logger.warning("goals route: error | type={} | detail={}", type(exc).__name__, str(exc))
        return GoalsResponseDTO(data=[]).model_dump()
