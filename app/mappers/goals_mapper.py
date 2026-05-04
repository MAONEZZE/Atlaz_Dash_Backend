from app.dtos.goals_dto import GoalsResponseDTO, SalesGoalsDTO


def map_to_goals_response(goals: list[SalesGoalsDTO]) -> GoalsResponseDTO:
    return GoalsResponseDTO(data=goals)
