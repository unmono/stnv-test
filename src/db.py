import os
import sqlite3
from contextlib import contextmanager
from typing import Callable, Any, Generator

from fastapi import HTTPException


RowFactoryType = Callable[[sqlite3.Cursor | sqlite3.Connection], tuple[Any, ...]]


@contextmanager
def sqlite_db(
        path_to_db: str | os.PathLike = "db.sqlite",
        row_factory: RowFactoryType | None = None,
) -> Generator[sqlite3.Connection]:
    try:
        conn = sqlite3.connect(
            path_to_db,
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