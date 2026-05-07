from app.dtos.goals_dto import GoalsResponseDTO, SalesGoalsDTO


def map_to_goals_response(goals_tuple: tuple[list[SalesGoalsDTO], float]) -> GoalsResponseDTO:
    goals, meta_faturamento_time = goals_tuple
    return GoalsResponseDTO(data=goals, meta_faturamento_time=meta_faturamento_time)
