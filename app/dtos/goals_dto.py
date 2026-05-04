from pydantic import BaseModel, Field
from typing import Literal


class SalesGoalsDTO(BaseModel):
    Nome: str = ""
    Cargo: str = ""
    Meta_Mensal: float = 0
    Meta_Numeros: int = 0
    Meta_Leads: int = 0
    Meta_Ligacoes: int = 0
    Meta_Reunioes: int = 0
    Meta_Indicacoes: int = 0


class TeamGoalsDTO(BaseModel):
    numeros_captados: int = 0
    ligacoes_agendadas: int = 0
    reunioes_agendadas: int = 0
    indicacoes: int = 0


class GoalsResponseDTO(BaseModel):
    data: list[SalesGoalsDTO] = Field(default_factory=list)


class TeamGoalsResponseDTO(BaseModel):
    data: list[TeamGoalsDTO] = Field(default_factory=list)

    @classmethod
    def empty(cls) -> "TeamGoalsResponseDTO":
        return cls(data=[TeamGoalsDTO()])
