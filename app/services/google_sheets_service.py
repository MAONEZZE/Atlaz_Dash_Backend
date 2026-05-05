import json as _json

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger

from app.core.config import settings
from app.core.exceptions import DataSourceError

# Hard-coded readonly scope — never allow write scopes here
_READONLY_SCOPE = "https://www.googleapis.com/auth/spreadsheets.readonly"

_service = None  # singleton — avoid recreating client on every request


def _build_service():
    raw = settings.google_application_credentials.strip()
    if raw.startswith("{"):
        info = _json.loads(raw)
        creds = service_account.Credentials.from_service_account_info(info, scopes=[_READONLY_SCOPE])
    else:
        creds = service_account.Credentials.from_service_account_file(raw, scopes=[_READONLY_SCOPE])
    assert _READONLY_SCOPE in creds.scopes, "Sheets credentials must use readonly scope only"
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def _get_service():
    global _service
    if _service is None:
        _service = _build_service()
    return _service


def read_tab(
    spreadsheet_id: str | None = None,
    tab_name: str = "Sheet1",
) -> list[list]:
    """Read a single tab and return raw cell matrix (list of rows, each row is list of values)."""
    sid = spreadsheet_id or settings.default_spreadsheet_id
    try:
        service = _get_service()
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=sid, range=tab_name)
            .execute()
        )
        return result.get("values", [])
    except HttpError as exc:
        logger.warning("Sheets HttpError | tab={} | status={} | detail={}", tab_name, exc.status_code, str(exc))
        raise DataSourceError("google_sheets", f"HTTP {exc.status_code} reading tab '{tab_name}'") from exc
    except FileNotFoundError as exc:
        logger.warning("Sheets credentials file not found: {}", settings.google_application_credentials)
        raise DataSourceError("google_sheets", "Credentials file not found") from exc
    except Exception as exc:
        logger.warning("Sheets unexpected error | tab={} | type={} | detail={}", tab_name, type(exc).__name__, str(exc))
        raise DataSourceError("google_sheets", f"Unexpected error reading tab '{tab_name}'") from exc


def read_tabs(
    tab_names: list[str],
    spreadsheet_id: str | None = None,
) -> dict[str, list[list]]:
    """Read multiple tabs in a single batchGet call. Returns dict keyed by tab name."""
    sid = spreadsheet_id or settings.default_spreadsheet_id
    try:
        service = _get_service()
        result = (
            service.spreadsheets()
            .values()
            .batchGet(spreadsheetId=sid, ranges=tab_names)
            .execute()
        )
        value_ranges = result.get("valueRanges", [])
        out: dict[str, list[list]] = {}
        for i, tab in enumerate(tab_names):
            vr = value_ranges[i] if i < len(value_ranges) else {}
            out[tab] = vr.get("values", [])
        return out
    except HttpError as exc:
        logger.warning("Sheets batchGet HttpError | tabs={} | status={}", tab_names, exc.status_code)
        raise DataSourceError("google_sheets", f"HTTP {exc.status_code} reading tabs {tab_names}") from exc
    except FileNotFoundError as exc:
        logger.warning("Sheets credentials file not found: {}", settings.google_application_credentials)
        raise DataSourceError("google_sheets", "Credentials file not found") from exc
    except Exception as exc:
        logger.warning("Sheets batchGet unexpected error | tabs={} | type={}", tab_names, type(exc).__name__)
        raise DataSourceError("google_sheets", f"Unexpected error reading tabs {tab_names}") from exc
