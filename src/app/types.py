import sqlite3
from typing import (
    Generator,
    Callable,
    TypeAlias,
    Any,
)


# type SqliteExecutable = sqlite3.Cursor | sqlite3.Connection
# type RowFactoryType = Callable[[sqlite3.Cursor | sqlite3.Connection], tuple[Any, ...]]
# type SQLiteContextManager = Generator[sqlite3.Connection]
SQLiteExecutable: TypeAlias = sqlite3.Cursor | sqlite3.Connection
RowFactoryType: TypeAlias = Callable[[SQLiteExecutable], tuple[Any, ...]]
SQLiteContextManager: TypeAlias = Generator[sqlite3.Connection, None, None]
CommentsAutoreplyData: TypeAlias = list[tuple[int, str, int, int]]