from pydantic import BaseModel, Field
from typing import Any


class UserInfoDTO(BaseModel):
    id: str = ""
    nome: str = ""
    cargo: str = ""
    imagem_url: str = ""


class UsersResponseDTO(BaseModel):
    data: list[UserInfoDTO] = Field(default_factory=list)


class UserStatisticsResponseDTO(BaseModel):
    user_id: str = ""
    nome: str = ""
    cargo: str = ""
    statistics: dict[str, Any] = Field(default_factory=lambda: {"CLOSER": [], "SDR": []})
