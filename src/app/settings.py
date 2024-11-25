import os
from functools import cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    google_key: str
    secret_key: str
    db_path: str | os.PathLike
    sql_init: str | os.PathLike


@cache
def get_settings() -> Settings:
    return Settings()
