import httpx
from loguru import logger

from app.core.config import settings

_EMPTY_RESPONSE: dict = {"SDR": [], "CLOSER": []}


def _validate_shape(data: object) -> bool:
    if not isinstance(data, dict):
        return False
    if "SDR" not in data or "CLOSER" not in data:
        return False
    if not isinstance(data["SDR"], list) or not isinstance(data["CLOSER"], list):
        return False
    return True


async def fetch_current_month_statistics() -> dict:
    """Fetch statistics from n8n for the current month. Never raises — returns empty on any failure."""
    url = settings.n8n_statistics_url
    timeout = float(settings.n8n_statistics_timeout_seconds)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException:
        logger.warning("n8n statistics: request timed out after {}s | url={}", timeout, url)
        return _EMPTY_RESPONSE
    except httpx.HTTPStatusError as exc:
        logger.warning("n8n statistics: HTTP {} | url={}", exc.response.status_code, url)
        return _EMPTY_RESPONSE
    except httpx.RequestError as exc:
        logger.warning("n8n statistics: network error | type={} | detail={}", type(exc).__name__, str(exc))
        return _EMPTY_RESPONSE
    except ValueError:
        logger.warning("n8n statistics: invalid JSON response | url={}", url)
        return _EMPTY_RESPONSE

    if not _validate_shape(data):
        logger.warning("n8n statistics: unexpected response shape | keys={}", list(data.keys()) if isinstance(data, dict) else type(data))
        return _EMPTY_RESPONSE

    return data
