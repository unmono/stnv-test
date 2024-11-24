import os
from functools import cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='./.env',
    )

    google_key: str = 'bla'
    secret_key: str
    db_path: str | os.PathLike
    sql_init: str | os.PathLike = './init.sql'


@cache
def get_settings() -> Settings:
    return Settings()
