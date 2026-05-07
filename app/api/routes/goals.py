from fastapi import APIRouter, Depends
from loguru import logger

from app.core.auth import require_auth
from app.dtos.goals_dto import GoalsResponseDTO
from app.mappers.goals_mapper import map_to_goals_response
from app.repositories.goals_repository import fetch_goals_raw
from app.services.goals_service import parse_goals

router = APIRouter()

_EMPTY_TEAM_GOALS = {
    "SDR":    {"numeros_captados": 0, "ligacoes_agendadas": 0, "abordagens": 0, "indicacoes_captadas": 0},
    "Closer": {"ligacoes_realizadas": 0, "reunioes_agendadas": 0, "reunioes_realizadas": 0, "indicacoes": 0},
}


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


@router.get("/goals/metrics", response_model=None, dependencies=[Depends(require_auth)])
async def get_goals_metrics() -> dict:
    """Return summed metric goals per role (SDR / Closer) from METAS sheet.

    Shape: { SDR: {...}, Closer: {...} } — no data wrapper, consumed directly by useTeamGoals.
    """
    try:
        matrix = fetch_goals_raw()
        goals, _ = parse_goals(matrix)

        sdr: dict[str, int] = {"numeros_captados": 0, "ligacoes_agendadas": 0, "abordagens": 0, "indicacoes_captadas": 0}
        closer: dict[str, int] = {"ligacoes_realizadas": 0, "reunioes_agendadas": 0, "reunioes_realizadas": 0, "indicacoes": 0}

        for g in goals:
            if g.Cargo == "SDR":
                sdr["numeros_captados"]  += g.Meta_Numeros
                sdr["ligacoes_agendadas"] += g.Meta_Ligacoes
                sdr["indicacoes_captadas"] += g.Meta_Indicacoes
            elif g.Cargo == "Closer":
                closer["ligacoes_realizadas"] += g.Meta_Ligacoes
                closer["reunioes_agendadas"]  += g.Meta_Reunioes
                closer["indicacoes"]          += g.Meta_Indicacoes

        return {"SDR": sdr, "Closer": closer}
    except Exception as exc:
        logger.warning("goals/metrics route: error | type={} | detail={}", type(exc).__name__, str(exc))
        return _EMPTY_TEAM_GOALS
