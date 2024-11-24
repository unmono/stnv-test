import os
import sqlite3
from contextlib import contextmanager
from functools import partial
from typing import Annotated

from fastapi import HTTPException, Depends

from .settings import get_settings, Settings
from .types import RowFactoryType, SQLiteContextManager


@contextmanager
def sqlite_cm(
        db_path: str | os.PathLike,
        row_factory: RowFactoryType | None = None,
) -> SQLiteContextManager:
    try:
        conn = sqlite3.connect(db_path)
    except sqlite3.Error as err:
        # logger.critical(f'Database is out of reach. Says:\n{err}')
        raise err
    if row_factory is not None:
        conn.row_factory = row_factory
    try:
        yield conn
    finally:
        conn.close()


def initialize_db(settings: Settings):
    with sqlite_cm(settings.db_path, None) as db:
        with open(settings.sql_init, 'r') as f:
            db.executescript(f.read())
        db.commit()


def prepare_db(settings: Annotated[Settings, Depends(get_settings)]):
    return partial[SQLiteContextManager](sqlite_cm, db_path=settings.db_path)
