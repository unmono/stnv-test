import os
from functools import cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='./.env',
    )

    secret_key: str
    db_path: str | os.PathLike


@cache
def get_settings() -> Settings:
    return Settings()
