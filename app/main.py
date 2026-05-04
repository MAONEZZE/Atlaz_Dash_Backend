from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import DataSourceError, data_source_exception_handler, unhandled_exception_handler
import app.core.logging  # noqa: F401 — initializes loguru

from app.api.routes import health, statistics, goals, users, sales_values, pre_sales, sheets_debug

app = FastAPI(title="Atlaz Dash Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(DataSourceError, data_source_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(health.router)
app.include_router(statistics.router)
app.include_router(goals.router)
app.include_router(users.router)
app.include_router(sales_values.router)
app.include_router(pre_sales.router)
app.include_router(sheets_debug.router)
