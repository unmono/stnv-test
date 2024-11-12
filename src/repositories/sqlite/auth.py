import sqlite3

from .base import SqliteRepositoryBase
from ..exceptions import NoEntry, AlreadyExists


class SqliteAuthRepository(SqliteRepositoryBase):
    def register_user(self, email: str, hashed_pass: str) -> None:
        try:
            with self.db() as db:
                db.execute(
                    "INSERT INTO users(email, hash) "
                    "VALUES (?, ?);",
                    (email, hashed_pass)
                )
                db.commit()
        except sqlite3.IntegrityError as err:
            if 'unique constraint' in err.args[0].lower():
                raise AlreadyExists('Such email has already been stored')
            raise err

    def get_user_credentials(self, email: str) -> tuple[int, str]:
        with self.db() as db:
            result = db.execute(
                "SELECT rowid as id, hash "
                "FROM users "
                "WHERE email = ? "
                "LIMIT 1;",
                (email,)
            )
            if id_and_hash := result.fetchone():
                return id_and_hash
            raise NoEntry()
