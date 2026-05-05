"""
Google Sheets service — read-only.

Uses google.auth + requests (not httplib2/googleapiclient) to avoid
socket timeout issues with httplib2 in certain environments.
"""

import json as _json
from urllib.parse import quote as _quote

import requests as _requests
from google.auth.transport.requests import AuthorizedSession, Request
from google.oauth2 import service_account
from loguru import logger

from app.core.config import settings
from app.core.exceptions import DataSourceError

# Hard-coded readonly scope — never allow write scopes here
_READONLY_SCOPE = "https://www.googleapis.com/auth/spreadsheets.readonly"
_SHEETS_BASE = "https://sheets.googleapis.com/v4/spreadsheets"

_session: AuthorizedSession | None = None


def _resolve_credentials() -> service_account.Credentials:
    """
    Load service account credentials from env vars.
    Priority: GOOGLE_SHEETS_CREDENTIALS_JSON > GOOGLE_APPLICATION_CREDENTIALS (both accept inline JSON or file path).
    """
    candidates = [
        settings.google_sheets_credentials_json.strip(),
        settings.google_application_credentials.strip(),
    ]

    for raw in candidates:
        if not raw:
            continue
        if raw.startswith("{"):
            try:
                info = _json.loads(raw)
            except _json.JSONDecodeError as exc:
                raise DataSourceError("google_sheets", f"Credentials env var is not valid JSON: {exc}") from exc
            return service_account.Credentials.from_service_account_info(info, scopes=[_READONLY_SCOPE])
        return service_account.Credentials.from_service_account_file(raw, scopes=[_READONLY_SCOPE])

    raise DataSourceError(
        "google_sheets",
        "No credentials configured. Set GOOGLE_SHEETS_CREDENTIALS_JSON or GOOGLE_APPLICATION_CREDENTIALS.",
    )


def _get_session() -> AuthorizedSession:
    global _session
    if _session is None:
        try:
            creds = _resolve_credentials()
            assert _READONLY_SCOPE in creds.scopes, "Sheets credentials must use readonly scope only"
            _session = AuthorizedSession(creds)
        except Exception:
            _session = None
            raise
    return _session


def _get(url: str) -> dict:
    """Execute authenticated GET, raise DataSourceError on failure."""
    try:
        session = _get_session()
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except _requests.HTTPError as exc:
        logger.warning("Sheets HTTP error | url={} | status={}", url, exc.response.status_code)
        raise DataSourceError("google_sheets", f"HTTP {exc.response.status_code}") from exc
    except _requests.RequestException as exc:
        logger.warning("Sheets request error | url={} | type={} | detail={}", url, type(exc).__name__, str(exc))
        # Reset session so next call retries auth
        global _session
        _session = None
        raise DataSourceError("google_sheets", f"Request error: {exc}") from exc
    except Exception as exc:
        logger.warning("Sheets unexpected error | url={} | type={} | detail={}", url, type(exc).__name__, str(exc))
        _session = None
        raise DataSourceError("google_sheets", f"Unexpected error: {exc}") from exc


def read_tab(
    spreadsheet_id: str | None = None,
    tab_name: str = "Sheet1",
) -> list[list]:
    """Read a single tab and return raw cell matrix."""
    sid = spreadsheet_id or settings.default_spreadsheet_id
    url = f"{_SHEETS_BASE}/{sid}/values/{_quote(tab_name)}"
    try:
        data = _get(url)
        return data.get("values", [])
    except DataSourceError:
        raise
    except Exception as exc:
        raise DataSourceError("google_sheets", f"Unexpected error reading tab '{tab_name}'") from exc


def read_tabs(
    tab_names: list[str],
    spreadsheet_id: str | None = None,
) -> dict[str, list[list]]:
    """Read multiple tabs in a single batchGet call. Returns dict keyed by tab name."""
    sid = spreadsheet_id or settings.default_spreadsheet_id
    ranges_param = "&".join(f"ranges={_quote(t)}" for t in tab_names)
    url = f"{_SHEETS_BASE}/{sid}/values:batchGet?{ranges_param}"
    try:
        data = _get(url)
        value_ranges = data.get("valueRanges", [])
        out: dict[str, list[list]] = {}
        for i, tab in enumerate(tab_names):
            vr = value_ranges[i] if i < len(value_ranges) else {}
            out[tab] = vr.get("values", [])
        return out
    except DataSourceError:
        raise
    except Exception as exc:
        raise DataSourceError("google_sheets", f"Unexpected error reading tabs {tab_names}") from exc
