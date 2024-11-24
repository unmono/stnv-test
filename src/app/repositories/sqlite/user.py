import sqlite3

from ...schemas import User
from ..exceptions import NoEntry
from .base import SqliteRepositoryBase


def user_factory(cursor: sqlite3.Cursor | sqlite3.Connection, row: tuple[any, ...]) -> User:
    kw = {
        column[0]: row[idx]
        for idx, column in enumerate(cursor.description)
    }
    return User(**kw)


class SqliteUserRepository(SqliteRepositoryBase):
    def _setup(self):
        self.row_factory = user_factory

    def get(self, user_id: int) -> User:
        with self.db(row_factory=user_factory) as db:
            result = db.execute(
                "SELECT rowid as user_id, email, autoreply_timeout "
                "FROM users "
                "WHERE rowid = ? "
                "LIMIT 1;",
                (user_id, ),
            )
            if user := result.fetchone():
                return user
        raise NoEntry('No such user')


    def save(self, user: User) -> User:
        with self.db(row_factory=user_factory) as db:
            cursor = db.execute(
                "UPDATE users "
                "SET email = ?, autoreply_timeout = ? "
                "WHERE rowid = ? "
                "RETURNING rowid as user_id, email, autoreply_timeout;",
                (user.email, user.autoreply_timeout, user.user_id),
            )
            if user := cursor.fetchone():
                db.commit()
                return user
            raise NoEntry


    def delete(self, user_id: int) -> User:
        with self.db(row_factory=user_factory) as db:
            result = db.execute(
                "DELETE FROM users "
                "WHERE rowid = ? "
                "RETURNING *;",
                (user_id, ),
            )
            db.commit()
        return result.fetchone()
