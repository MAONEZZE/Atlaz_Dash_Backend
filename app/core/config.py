from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Google Sheets credentials (file path or inline JSON)
    google_application_credentials: str = ""
    google_sheets_credentials_json: str = ""
    google_sheets_scopes: str = "https://www.googleapis.com/auth/spreadsheets.readonly"

    # Main spreadsheet (Planilha Isaac Newton — BASE_VENDAS, METAS, FATURAMENTO, etc.)
    default_spreadsheet_id: str = "1NrKYW3BByJJ688ILwG20AvBuc-YggkwkOun34Ewjwck"

    # Per-seller spreadsheet IDs — each has a "Métricas Diárias" tab
    # Set these in .env after getting the IDs from Google Sheets
    sheet_id_linkedin_jonathan: str = ""  # "Linkedin Jonathan | SDR: Tay | Closer: Jonathan"
    sheet_id_linkedin_jacob: str = ""     # "Linkedin Jacob | SDR: Jenni | Closer: Jacob"
    sheet_id_linkedin_alex: str = ""      # "Linkedin Alex | SDR: Jenni | Closer: Alex"
    daily_metrics_tab_name: str = "Métricas Diárias"

    # Database
    database_url: str = ""

    # JWT auth
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # CORS
    cors_origins: str = "https://dash.learningbrands.cloud"

    # n8n statistics webhook
    n8n_statistics_url: str = ""
    n8n_statistics_timeout_seconds: int = 30

    # Sales finance route API key (legacy — kept for server-to-server use)
    sales_api_key: str = ""

    debug_routes_enabled: bool = False

    # Profile image tokens for dash_users
    vite_img_jacob_token: str = ""
    vite_img_jonathan_token: str = ""
    vite_img_alex_token: str = ""
    vite_img_jennifer_token: str = ""
    vite_img_tayrone_token: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def sheets_scopes_list(self) -> list[str]:
        return [s.strip() for s in self.google_sheets_scopes.split(",") if s.strip()]

    def image_token_for(self, name: str) -> str:
        key = f"vite_img_{name.lower()}_token"
        return getattr(self, key, "")

    @property
    def daily_metrics_sources(self) -> list[dict]:
        """Return list of {sheet_id, closer, sdr} for daily metrics reading. Skips unconfigured."""
        sources = [
            {"sheet_id": self.sheet_id_linkedin_jonathan, "closer": "Jonathan", "sdr": "Tayrone"},
            {"sheet_id": self.sheet_id_linkedin_jacob,    "closer": "Jacob",    "sdr": "Jennifer"},
            {"sheet_id": self.sheet_id_linkedin_alex,     "closer": "Alex",     "sdr": "Jennifer"},
        ]
        return [s for s in sources if s["sheet_id"]]


settings = Settings()
