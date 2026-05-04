from fastapi import APIRouter
from loguru import logger

from app.dtos.goals_dto import TeamGoalsDTO, TeamGoalsResponseDTO
from app.dtos.users_dto import UsersResponseDTO, UserStatisticsResponseDTO
from app.mappers.statistics_mapper import map_to_statistic_response
from app.repositories.goals_repository import fetch_goals_raw
from app.services.goals_service import parse_goals
from app.services.statistics_service import get_statistics
from app.services.team_service import compute_team_realized
from app.services.user_service import get_users, get_user_by_id

router = APIRouter()


@router.get("/users", response_model=None)
async def list_users() -> dict:
    """Return all users with id, name, role (lowercase), and image URL."""
    try:
        matrix = fetch_goals_raw()
        goals = parse_goals(matrix)
        users = get_users(goals)
        return UsersResponseDTO(data=users).model_dump()
    except Exception as exc:
        logger.warning("users route: error | type={} | detail={}", type(exc).__name__, str(exc))
        return UsersResponseDTO(data=[]).model_dump()


@router.get("/users/{user_id}/statistics", response_model=None)
async def user_statistics(user_id: str) -> dict:
    """Return statistics for a single user by id."""
    try:
        stats = await get_statistics(responsible=user_id)
        user = get_user_by_id(user_id)
        response = map_to_statistic_response(stats)
        return UserStatisticsResponseDTO(
            user_id=user_id,
            nome=user.nome if user else user_id,
            cargo=user.cargo if user else "",
            statistics=response.data[0] if response.data else {"CLOSER": [], "SDR": []},
        ).model_dump()
    except Exception as exc:
        logger.warning("user_statistics route: error | user_id={} | type={} | detail={}", user_id, type(exc).__name__, str(exc))
        return UserStatisticsResponseDTO(
            user_id=user_id,
            nome=user_id,
            cargo="",
            statistics={"CLOSER": [], "SDR": []},
        ).model_dump()


@router.get("/team/realized", response_model=None)
async def team_realized() -> dict:
    """Return aggregated team realized totals (SDR metrics summed)."""
    try:
        stats = await get_statistics()
        total = compute_team_realized(stats)
        return TeamGoalsResponseDTO(data=[total]).model_dump()
    except Exception as exc:
        logger.warning("team_realized route: error | type={} | detail={}", type(exc).__name__, str(exc))
        return TeamGoalsResponseDTO.empty().model_dump()
