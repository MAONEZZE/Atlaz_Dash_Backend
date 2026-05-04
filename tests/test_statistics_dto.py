from app.dtos.statistics_dto import FrontendCloserStatisticDTO, FrontendSdrStatisticDTO, StatisticResponseDTO
from app.mappers.statistics_mapper import map_to_statistic_response
from app.services.statistics_service import NormalizedStatistics, NormalizedCloserStats, NormalizedSdrStats


def test_closer_dto_field_names():
    dto = FrontendCloserStatisticDTO(Nome="Jacob", ligacoes_realizadas=3, reunioes_agendadas=1, reunioes_realizadas=1, indicacoes=0)
    out = dto.to_frontend()
    assert "Ligações\nRealizadas" in out
    assert "Reuniões\nAgendadas" in out
    assert "Reuniões\nRealizadas" in out
    assert "Indicações" in out
    assert out["Ligações\nRealizadas"] == 3


def test_sdr_dto_field_names():
    dto = FrontendSdrStatisticDTO(Nome="Jennifer", conexoes_enviadas=10, follow_ups=2)
    out = dto.to_frontend()
    assert "Conexões\nEnviadas" in out
    assert "Follow-ups" in out
    assert "Números\nCaptados" in out
    assert out["Conexões\nEnviadas"] == 10
    assert out["Números\nCaptados"] == 0  # default


def test_empty_response():
    resp = StatisticResponseDTO.empty()
    assert resp.data == [{"CLOSER": [], "SDR": []}]


def test_map_to_statistic_response():
    stats = NormalizedStatistics(
        closer=[NormalizedCloserStats(nome="Jacob", ligacoes_realizadas=5, reunioes_agendadas=2)],
        sdr=[NormalizedSdrStats(nome="Jennifer", conexoes_enviadas=20, abordagens=10)],
    )
    resp = map_to_statistic_response(stats)
    assert len(resp.data) == 1
    closer = resp.data[0]["CLOSER"]
    sdr = resp.data[0]["SDR"]
    assert closer[0]["Nome"] == "Jacob"
    assert closer[0]["Ligações\nRealizadas"] == 5
    assert sdr[0]["Nome"] == "Jennifer"
    assert sdr[0]["Conexões\nEnviadas"] == 20


def test_missing_fields_default_zero():
    stats = NormalizedStatistics(
        closer=[NormalizedCloserStats(nome="Alex")],
        sdr=[],
    )
    resp = map_to_statistic_response(stats)
    closer = resp.data[0]["CLOSER"][0]
    assert closer["Ligações\nRealizadas"] == 0
    assert closer["Indicações"] == 0
