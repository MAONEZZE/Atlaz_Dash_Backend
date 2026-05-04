from app.dtos.statistics_dto import FrontendCloserStatisticDTO, FrontendSdrStatisticDTO, StatisticResponseDTO
from app.services.statistics_service import NormalizedStatistics


def map_to_statistic_response(stats: NormalizedStatistics) -> StatisticResponseDTO:
    closer_list = [
        FrontendCloserStatisticDTO(
            Nome=c.nome,
            ligacoes_realizadas=c.ligacoes_realizadas,
            reunioes_agendadas=c.reunioes_agendadas,
            reunioes_realizadas=c.reunioes_realizadas,
            indicacoes=c.indicacoes,
        ).to_frontend()
        for c in stats.closer
    ]

    sdr_list = [
        FrontendSdrStatisticDTO(
            Nome=s.nome,
            conexoes_enviadas=s.conexoes_enviadas,
            conexoes_aceitas=s.conexoes_aceitas,
            inmails_enviados=s.inmails_enviados,
            follow_ups=s.follow_ups,
            numeros_captados=s.numeros_captados,
            ligacoes_agendadas=s.ligacoes_agendadas,
            reunioes_agendadas=s.reunioes_agendadas,
            indicacoes_captadas=s.indicacoes_captadas,
            abordagens=s.abordagens,
        ).to_frontend()
        for s in stats.sdr
    ]

    return StatisticResponseDTO(data=[{"CLOSER": closer_list, "SDR": sdr_list}])
