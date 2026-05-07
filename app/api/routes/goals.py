from fastapi import APIRouter, Depends
from loguru import logger

from app.core.auth import require_auth
from app.dtos.goals_dto import GoalsResponseDTO
from app.mappers.goals_mapper import map_to_goals_response
from app.repositories.goals_repository import fetch_goals_raw
from app.services.goals_service import parse_goals

router = APIRouter()


@router.get("/goals/fat", response_model=None, dependencies=[Depends(require_auth)])
async def get_goals_fat() -> dict:
    """Return individual goals from METAS sheet tab (Planilha Isaac Newton)."""
    try:
        matrix = fetch_goals_raw()
        goals, meta_time = parse_goals(matrix)
        return map_to_goals_response((goals, meta_time)).model_dump()
    except Exception as exc:
        logger.warning("goals/fat route: error | type={} | detail={}", type(exc).__name__, str(exc))
        return GoalsResponseDTO(data=[]).model_dump()
