from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    google_application_credentials: str = "./credentials/service-account.json"
    google_sheets_scopes: str = "https://www.googleapis.com/auth/spreadsheets.readonly"
    default_spreadsheet_id: str = "1NrKYW3BByJJ688ILwG20AvBuc-YggkwkOun34Ewjwck"

    database_url: str = ""

    n8n_statistics_url: str = "https://n8n.learningbrands.cloud/webhook/statistic"
    n8n_statistics_timeout_seconds: int = 10

    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    debug_routes_enabled: bool = False

    vite_img_jacob_token: str = ""
    vite_img_jonathan_token: str = ""
    vite_img_alex_token: str = ""
    vite_img_jennifer_token: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def sheets_scopes_list(self) -> list[str]:
        return [s.strip() for s in self.google_sheets_scopes.split(",") if s.strip()]

    def image_token_for(self, name: str) -> str:
        key = f"vite_img_{name.lower()}_token"
        return getattr(self, key, "")


settings = Settings()
