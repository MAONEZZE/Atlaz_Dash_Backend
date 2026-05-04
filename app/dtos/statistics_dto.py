from pydantic import BaseModel, Field
from typing import Annotated


class FrontendCloserStatisticDTO(BaseModel):
    model_config = {"populate_by_name": True}

    Nome: str = ""
    ligacoes_realizadas: Annotated[int, Field(alias="Ligações\nRealizadas")] = 0
    reunioes_agendadas: Annotated[int, Field(alias="Reuniões\nAgendadas")] = 0
    reunioes_realizadas: Annotated[int, Field(alias="Reuniões\nRealizadas")] = 0
    indicacoes: Annotated[int, Field(alias="Indicações")] = 0

    def to_frontend(self) -> dict:
        return {
            "Nome": self.Nome,
            "Ligações\nRealizadas": self.ligacoes_realizadas,
            "Reuniões\nAgendadas": self.reunioes_agendadas,
            "Reuniões\nRealizadas": self.reunioes_realizadas,
            "Indicações": self.indicacoes,
        }


class FrontendSdrStatisticDTO(BaseModel):
    model_config = {"populate_by_name": True}

    Nome: str = ""
    conexoes_enviadas: int = 0
    conexoes_aceitas: int = 0
    inmails_enviados: int = 0
    follow_ups: int = 0
    numeros_captados: int = 0
    ligacoes_agendadas: int = 0
    reunioes_agendadas: int = 0
    indicacoes_captadas: int = 0
    abordagens: int = 0

    def to_frontend(self) -> dict:
        return {
            "Nome": self.Nome,
            "Conexões\nEnviadas": self.conexoes_enviadas,
            "Conexões\nAceitas": self.conexoes_aceitas,
            "InMails\nEnviados": self.inmails_enviados,
            "Follow-ups": self.follow_ups,
            "Números\nCaptados": self.numeros_captados,
            "Ligações\nAgendadas": self.ligacoes_agendadas,
            "Reuniões\nAgendadas": self.reunioes_agendadas,
            "Indicações\nCaptadas": self.indicacoes_captadas,
            "Abordagens": self.abordagens,
        }


class StatisticResponseDTO(BaseModel):
    data: list[dict] = Field(default_factory=list)

    @classmethod
    def empty(cls) -> "StatisticResponseDTO":
        return cls(data=[{"CLOSER": [], "SDR": []}])
