import pytest
from unittest.mock import patch
from app.services.statistics_service import (
    NormalizedStatistics,
    NormalizedCloserStats,
    _filter_by_user_id,
)

def _multi_stats():
    return NormalizedStatistics(
        closer=[
            NormalizedCloserStats(nome="Jacob", ligacoes_realizadas=5),
            NormalizedCloserStats(nome="Jonathan", ligacoes_realizadas=3),
        ],
        sdr=[],
    )

def test_filter_by_user_id_unknown_returns_empty():
    with patch("app.services.statistics_service.fetch_user_by_id", return_value=None):
        result = _filter_by_user_id(_multi_stats(), 999)
    assert result.closer == []
    assert result.sdr == []

def test_filter_by_user_id_known_filters_correctly():
    with patch("app.services.statistics_service.fetch_user_by_id", return_value={"nome": "Jacob"}):
        result = _filter_by_user_id(_multi_stats(), 1)
    assert len(result.closer) == 1
    assert result.closer[0].nome == "Jacob"

def test_filter_by_user_id_excludes_non_matching():
    with patch("app.services.statistics_service.fetch_user_by_id", return_value={"nome": "Jonathan"}):
        result = _filter_by_user_id(_multi_stats(), 2)
    assert len(result.closer) == 1
    assert result.closer[0].nome == "Jonathan"
