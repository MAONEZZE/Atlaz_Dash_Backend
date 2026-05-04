from pydantic import BaseModel, Field


class N8nSdrStatisticDTO(BaseModel):
    Nome: str = ""
    Conexoes_Enviadas: int = 0
    Conexoes_Aceitas: int = 0
    Abordagens: int = 0
    InMails_Enviados: int = 0
    Follow_ups: int = 0
    Numeros_Captados: int = 0
    Ligacoes_Agendadas: int = 0
    Indicacoes_Captadas: int = 0


class N8nCloserStatisticDTO(BaseModel):
    Nome: str = ""
    Ligacoes_Realizadas: int = 0
    Reunioes_Agendadas: int = 0
    Reunioes_Realizadas: int = 0
    Indicacoes: int = 0


class N8nStatisticsResponseDTO(BaseModel):
    SDR: list[N8nSdrStatisticDTO] = Field(default_factory=list)
    CLOSER: list[N8nCloserStatisticDTO] = Field(default_factory=list)
