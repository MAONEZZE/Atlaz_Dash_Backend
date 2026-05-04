from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger


class DataSourceError(Exception):
    def __init__(self, source: str, detail: str):
        self.source = source
        self.detail = detail
        super().__init__(f"[{source}] {detail}")


async def data_source_exception_handler(request: Request, exc: DataSourceError) -> JSONResponse:
    logger.warning("DataSourceError | source={} | path={} | detail={}", exc.source, request.url.path, exc.detail)
    return JSONResponse(status_code=200, content={"error": exc.detail, "data": []})


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception | path={} | type={} | detail={}", request.url.path, type(exc).__name__, str(exc))
    return JSONResponse(status_code=200, content={"error": "Internal error", "data": []})
