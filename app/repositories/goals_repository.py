from loguru import logger

from app.core.exceptions import DataSourceError
from app.services.google_sheets_service import read_tab
from app.core.config import settings


def fetch_goals_raw() -> list[list]:
    """Read METAS tab and return raw matrix. Raises DataSourceError on failure."""
    try:
        return read_tab(settings.default_spreadsheet_id, "METAS")
    except DataSourceError:
        raise
    except Exception as exc:
        logger.warning("goals_repository: unexpected error | detail={}", str(exc))
        raise DataSourceError("google_sheets", f"Failed to read METAS tab: {exc}") from exc
