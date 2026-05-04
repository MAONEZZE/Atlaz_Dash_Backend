import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.n8n_statistics_client import fetch_current_month_statistics

_GOOD_RESPONSE = {
    "SDR": [{"Nome": "Jennifer", "Conexoes_Enviadas": 5}],
    "CLOSER": [{"Nome": "Jacob", "Ligacoes_Realizadas": 2}],
}

pytestmark = pytest.mark.asyncio


async def _mock_get(url, **kwargs):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=_GOOD_RESPONSE)
    return resp


@pytest.mark.asyncio
async def test_success():
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=_mock_get)
        mock_client_cls.return_value = mock_client
        result = await fetch_current_month_statistics()
    assert "SDR" in result
    assert "CLOSER" in result
    assert len(result["SDR"]) == 1


@pytest.mark.asyncio
async def test_timeout_returns_empty():
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_client_cls.return_value = mock_client
        result = await fetch_current_month_statistics()
    assert result == {"SDR": [], "CLOSER": []}


@pytest.mark.asyncio
async def test_http_500_returns_empty():
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        resp = MagicMock()
        resp.status_code = 500
        exc = httpx.HTTPStatusError("500", request=MagicMock(), response=resp)
        resp.raise_for_status = MagicMock(side_effect=exc)
        mock_client.get = AsyncMock(return_value=resp)
        mock_client_cls.return_value = mock_client
        result = await fetch_current_month_statistics()
    assert result == {"SDR": [], "CLOSER": []}


@pytest.mark.asyncio
async def test_malformed_json_returns_empty():
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json = MagicMock(side_effect=ValueError("bad json"))
        mock_client.get = AsyncMock(return_value=resp)
        mock_client_cls.return_value = mock_client
        result = await fetch_current_month_statistics()
    assert result == {"SDR": [], "CLOSER": []}


@pytest.mark.asyncio
async def test_missing_keys_returns_empty():
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json = MagicMock(return_value={"WRONG_KEY": []})
        mock_client.get = AsyncMock(return_value=resp)
        mock_client_cls.return_value = mock_client
        result = await fetch_current_month_statistics()
    assert result == {"SDR": [], "CLOSER": []}
