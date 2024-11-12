import sqlite3
from typing import Generator, Annotated


type SqliteGenerator = Generator[sqlite3.Connection, None, None]
type SqliteExecutable = sqlite3.Cursor | sqlite3.Connection