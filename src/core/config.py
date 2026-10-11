from pathlib import Path
from pydantic import BaseModel, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class ApiConfig(BaseModel):
    """Функция для настройки routs"""

    prefix: str = "/api"


class DatabaseConfig(BaseModel):
    url: str | PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 5
    max_overflow: int = 10

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str | PostgresDsn) -> str:
        return str(v)

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }


class RunConfig(BaseModel):
    host: str = "0.0.0.0"  # noqa:S104
    port: int = 8000
    reload: bool = True


class AppConfig(BaseModel):
    title: str = "Kvitto"
    version: str = "0.1.0"
    description: str = "Kvitto"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
        extra="ignore",
    )
    app: AppConfig = AppConfig()
    run: RunConfig = RunConfig()
    db: DatabaseConfig
    api: ApiConfig = ApiConfig()


settings = Settings()
