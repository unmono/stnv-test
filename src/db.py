import os
import sqlite3
from contextlib import contextmanager
from functools import partial
from typing import Callable, Any, Generator, Annotated

from fastapi import HTTPException, Depends

from .settings import get_settings, Settings


type RowFactoryType = Callable[[sqlite3.Cursor | sqlite3.Connection], tuple[Any, ...]]
type SQLiteContextManager = Generator[sqlite3.Connection]


@contextmanager
def sqlite_cm(
        db_path: str | os.PathLike,
        row_factory: RowFactoryType | None = None,
) -> SQLiteContextManager:
    try:
        conn = sqlite3.connect(
            db_path,
            autocommit=False,
        )
    except sqlite3.Error as err:
        # logger.critical(f'Database is out of reach. Says:\n{err}')
        raise HTTPException(status_code=500, detail="Internal Server Error")
    if row_factory is not None:
        conn.row_factory = row_factory
    try:
        yield conn
    finally:
        conn.close()


def prepare_db(settings: Annotated[Settings, Depends(get_settings)]):
    return partial[SQLiteContextManager](sqlite_cm, db_path=settings.db_path)
