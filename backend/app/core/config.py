from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "fastapi-vue-admin-scaffold"
    database_url: str = "sqlite:///./dev.db"
    jwt_secret: str = "dev-only-secret-change-before-deploy"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    cors_origins: str = "http://localhost:5173"
    seed_on_startup: bool = True
    auto_create_tables: bool = True
    scheduler_enabled: bool = True
    scheduler_timezone: str = "Asia/Shanghai"
    operation_log_retention_days: int = 180

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]
