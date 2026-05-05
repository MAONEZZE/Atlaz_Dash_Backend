from typing import Optional

from fastapi import APIRouter, Query
from loguru import logger

from app.dtos.goals_dto import TeamGoalsResponseDTO
from app.dtos.users_dto import UsersResponseDTO, UserStatisticsResponseDTO
from app.mappers.statistics_mapper import map_to_statistic_response
from app.services.statistics_service import get_statistics
from app.services.team_service import compute_team_realized
from app.services.user_service import get_users, get_user_by_id

router = APIRouter()


@router.get("/users", response_model=None)
async def list_users() -> dict:
    """Return all users from dash_users table with id, name, role, and image URL."""
    try:
        users = get_users()
        return UsersResponseDTO(data=users).model_dump()
    except Exception as exc:
        logger.warning("users route: error | type={} | detail={}", type(exc).__name__, str(exc))
        return UsersResponseDTO(data=[]).model_dump()


@router.get("/users/{user_id}/statistics", response_model=None)
async def user_statistics(
    user_id: int,
    data_inicio: Optional[int] = Query(default=None, description="Início do período (timestamp ms)"),
    data_fim: Optional[int] = Query(default=None, description="Fim do período (timestamp ms)"),
) -> dict:
    """Return statistics for a single user by dash_users.id."""
    try:
        stats = await get_statistics(start_ms=data_inicio, end_ms=data_fim, responsavel=str(user_id))
        user = get_user_by_id(str(user_id))
        response = map_to_statistic_response(stats)
        return UserStatisticsResponseDTO(
            user_id=str(user_id),
            nome=user.nome if user else str(user_id),
            cargo=user.cargo if user else "",
            statistics=response.data[0] if response.data else {"CLOSER": [], "SDR": []},
        ).model_dump()
    except Exception as exc:
        logger.warning("user_statistics route: error | user_id={} | type={} | detail={}", user_id, type(exc).__name__, str(exc))
        return UserStatisticsResponseDTO(
            user_id=str(user_id),
            nome=str(user_id),
            cargo="",
            statistics={"CLOSER": [], "SDR": []},
        ).model_dump()


@router.get("/team/realized", response_model=None)
async def team_realized(
    data_inicio: Optional[int] = Query(default=None),
    data_fim: Optional[int] = Query(default=None),
) -> dict:
    """Return aggregated team realized totals (SDR metrics summed)."""
    try:
        stats = await get_statistics(start_ms=data_inicio, end_ms=data_fim)
        total = compute_team_realized(stats)
        return TeamGoalsResponseDTO(data=[total]).model_dump()
    except Exception as exc:
        logger.warning("team_realized route: error | type={} | detail={}", type(exc).__name__, str(exc))
        return TeamGoalsResponseDTO.empty().model_dump()
