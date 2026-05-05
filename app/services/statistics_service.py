from dataclasses import dataclass, field
from typing import Optional

from loguru import logger

from app.core.field_maps import resolve_name
from app.repositories.historical_statistics_repository import fetch_historical_statistics
from app.services.n8n_statistics_client import fetch_current_month_statistics
from app.services.period_service import classify_period
from app.utils.normalize_number import normalize_number


@dataclass
class NormalizedSdrStats:
    nome: str
    conexoes_enviadas: int = 0
    conexoes_aceitas: int = 0
    abordagens: int = 0
    inmails_enviados: int = 0
    follow_ups: int = 0
    numeros_captados: int = 0
    ligacoes_agendadas: int = 0
    reunioes_agendadas: int = 0
    indicacoes_captadas: int = 0


@dataclass
class NormalizedCloserStats:
    nome: str
    ligacoes_realizadas: int = 0
    reunioes_agendadas: int = 0
    reunioes_realizadas: int = 0
    indicacoes: int = 0


@dataclass
class NormalizedStatistics:
    sdr: list[NormalizedSdrStats] = field(default_factory=list)
    closer: list[NormalizedCloserStats] = field(default_factory=list)


def _merge_sdr(a: NormalizedSdrStats, b: NormalizedSdrStats) -> NormalizedSdrStats:
    return NormalizedSdrStats(
        nome=a.nome,
        conexoes_enviadas=a.conexoes_enviadas + b.conexoes_enviadas,
        conexoes_aceitas=a.conexoes_aceitas + b.conexoes_aceitas,
        abordagens=a.abordagens + b.abordagens,
        inmails_enviados=a.inmails_enviados + b.inmails_enviados,
        follow_ups=a.follow_ups + b.follow_ups,
        numeros_captados=a.numeros_captados + b.numeros_captados,
        ligacoes_agendadas=a.ligacoes_agendadas + b.ligacoes_agendadas,
        reunioes_agendadas=a.reunioes_agendadas + b.reunioes_agendadas,
        indicacoes_captadas=a.indicacoes_captadas + b.indicacoes_captadas,
    )


def _merge_closer(a: NormalizedCloserStats, b: NormalizedCloserStats) -> NormalizedCloserStats:
    return NormalizedCloserStats(
        nome=a.nome,
        ligacoes_realizadas=a.ligacoes_realizadas + b.ligacoes_realizadas,
        reunioes_agendadas=a.reunioes_agendadas + b.reunioes_agendadas,
        reunioes_realizadas=a.reunioes_realizadas + b.reunioes_realizadas,
        indicacoes=a.indicacoes + b.indicacoes,
    )


def _n8n_to_normalized(raw: dict) -> NormalizedStatistics:
    sdr_list: list[NormalizedSdrStats] = []
    for item in raw.get("SDR", []):
        nome = resolve_name(str(item.get("Nome", "")))
        sdr_list.append(NormalizedSdrStats(
            nome=nome,
            conexoes_enviadas=int(normalize_number(item.get("Conexoes_Enviadas", 0))),
            conexoes_aceitas=int(normalize_number(item.get("Conexoes_Aceitas", 0))),
            abordagens=int(normalize_number(item.get("Abordagens", 0))),
            inmails_enviados=int(normalize_number(item.get("InMails_Enviados", 0))),
            follow_ups=int(normalize_number(item.get("Follow_ups", 0))),
            numeros_captados=int(normalize_number(item.get("Numeros_Captados", 0))),
            ligacoes_agendadas=int(normalize_number(item.get("Ligacoes_Agendadas", 0))),
            reunioes_agendadas=0,
            indicacoes_captadas=int(normalize_number(item.get("Indicacoes_Captadas", 0))),
        ))

    closer_list: list[NormalizedCloserStats] = []
    for item in raw.get("CLOSER", []):
        nome = resolve_name(str(item.get("Nome", "")))
        closer_list.append(NormalizedCloserStats(
            nome=nome,
            ligacoes_realizadas=int(normalize_number(item.get("Ligacoes_Realizadas", 0))),
            reunioes_agendadas=int(normalize_number(item.get("Reunioes_Agendadas", 0))),
            reunioes_realizadas=int(normalize_number(item.get("Reunioes_Realizadas", 0))),
            indicacoes=int(normalize_number(item.get("Indicacoes", 0))),
        ))

    return NormalizedStatistics(sdr=sdr_list, closer=closer_list)


def _db_rows_to_normalized(rows: list[dict]) -> NormalizedStatistics:
    sdr_list: list[NormalizedSdrStats] = []
    closer_list: list[NormalizedCloserStats] = []

    for row in rows:
        nome = resolve_name(str(row.get("Nome", "")))
        role = str(row.get("role", "")).lower().strip()
        if role == "sdr":
            sdr_list.append(NormalizedSdrStats(
                nome=nome,
                conexoes_enviadas=int(normalize_number(row.get("conexoes_enviadas", 0))),
                conexoes_aceitas=int(normalize_number(row.get("conexoes_aceitas", 0))),
                abordagens=int(normalize_number(row.get("abordagens", 0))),
                inmails_enviados=int(normalize_number(row.get("inmails_enviados", 0))),
                follow_ups=int(normalize_number(row.get("follow_ups", 0))),
                numeros_captados=int(normalize_number(row.get("numeros_captados", 0))),
                ligacoes_agendadas=int(normalize_number(row.get("ligacoes_agendadas", 0))),
                reunioes_agendadas=int(normalize_number(row.get("reunioes_agendadas", 0))),
                indicacoes_captadas=int(normalize_number(row.get("indicacoes", 0))),
            ))
        elif role == "closer":
            closer_list.append(NormalizedCloserStats(
                nome=nome,
                ligacoes_realizadas=int(normalize_number(row.get("ligacoes_realizadas", 0))),
                reunioes_agendadas=int(normalize_number(row.get("reunioes_agendadas", 0))),
                reunioes_realizadas=int(normalize_number(row.get("reunioes_realizadas", 0))),
                indicacoes=int(normalize_number(row.get("indicacoes", 0))),
            ))

    return NormalizedStatistics(sdr=sdr_list, closer=closer_list)


def _consolidate(a: NormalizedStatistics, b: NormalizedStatistics) -> NormalizedStatistics:
    sdr_map: dict[str, NormalizedSdrStats] = {s.nome: s for s in a.sdr}
    for s in b.sdr:
        if s.nome in sdr_map:
            sdr_map[s.nome] = _merge_sdr(sdr_map[s.nome], s)
        else:
            sdr_map[s.nome] = s

    closer_map: dict[str, NormalizedCloserStats] = {c.nome: c for c in a.closer}
    for c in b.closer:
        if c.nome in closer_map:
            closer_map[c.nome] = _merge_closer(closer_map[c.nome], c)
        else:
            closer_map[c.nome] = c

    return NormalizedStatistics(
        sdr=list(sdr_map.values()),
        closer=list(closer_map.values()),
    )


async def get_statistics(
    start_ms: Optional[int] = None,
    end_ms: Optional[int] = None,
    channel: Optional[str] = None,
    responsible: Optional[str] = None,
    product: Optional[str] = None,
    stage: Optional[str] = None,
    status: Optional[str] = None,
    revenue_type: Optional[str] = None,
    ticket_range: Optional[str] = None,
    activity: Optional[str] = None,
) -> NormalizedStatistics:
    period = classify_period(start_ms, end_ms)

    current_stats = NormalizedStatistics()
    past_stats = NormalizedStatistics()

    if period.current:
        try:
            raw = await fetch_current_month_statistics()
            current_stats = _n8n_to_normalized(raw)
        except Exception as exc:
            logger.warning("statistics_service: n8n fetch failed | type={} | detail={}", type(exc).__name__, str(exc))

    if period.past and period.past_range:
        try:
            rows = fetch_historical_statistics(
                start_date=period.past_range[0],
                end_date=period.past_range[1],
                channel=channel,
                responsible=responsible,
                product=product,
                stage=stage,
                status=status,
                revenue_type=revenue_type,
                ticket_range=ticket_range,
                activity=activity,
            )
            past_stats = _db_rows_to_normalized(rows)
        except Exception as exc:
            logger.warning("statistics_service: DB fetch failed | type={} | detail={}", type(exc).__name__, str(exc))

    return _consolidate(current_stats, past_stats)
