from app.dtos.goals_dto import TeamGoalsDTO
from app.services.statistics_service import NormalizedStatistics


def compute_team_realized(stats: NormalizedStatistics) -> TeamGoalsDTO:
    """Aggregate realized totals across all SDR members."""
    return TeamGoalsDTO(
        numeros_captados=sum(s.numeros_captados for s in stats.sdr),
        ligacoes_agendadas=sum(s.ligacoes_agendadas for s in stats.sdr),
        reunioes_agendadas=sum(s.reunioes_agendadas for s in stats.sdr),
        indicacoes=sum(s.indicacoes_captadas for s in stats.sdr),
    )
