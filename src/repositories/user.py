import sqlite3

from argon2 import PasswordHasher

from ..schemas import User, UserCredentials
from ..db import sqlite_db
from ..exceptions import UserAlreadyExists, NoSuchUser


def hash_password_argon(password: str) -> str:
    ph = PasswordHasher()
    return ph.hash(password)


def user_factory(cursor: sqlite3.Cursor | sqlite3.Connection, row: tuple[any, ...]) -> User:
    kw = {
        column[0]: row[idx]
        for idx, column in enumerate(cursor.description)
    }
    return User(**kw)


def create_user(credentials: UserCredentials) -> User:
    hashed_password = hash_password_argon(credentials.password)
    try:
        with sqlite_db(row_factory=user_factory) as db:
            result = db.execute(
                "INSERT INTO users(email, hash) "
                "VALUES (?, ?) "
                "RETURNING rowid as user_id, email, autoreply_timeout;",
                (credentials.email, hashed_password),
            )
            user: User = result.fetchone()
            db.commit()
    except sqlite3.IntegrityError as err:
        if 'unique constraint' in err.args[0].lower():
            raise UserAlreadyExists('Such user already exists')
        raise err
    return user

def get_user(user_id: int) -> User:
    with sqlite_db(row_factory=user_factory) as db:
        result = db.execute(
            "SELECT rowid as user_id, email, autoreply_timeout "
            "FROM users "
            "WHERE rowid = ? "
            "LIMIT 1;",
            (user_id, ),
        )
        if user := result.fetchone():
            return user
    raise NoSuchUser('No such user')


def save_user(user: User) -> None:
    with sqlite_db() as db:
        db.execute(
            "UPDATE users "
            "SET email = ?, autoreply_timeout = ? "
            "WHERE rowid = ?;",
            (user.email, user.autoreply_timeout, user.user_id),
        )
        db.commit()


def delete_user(user_id: int) -> User:
    with sqlite_db(row_factory=user_factory) as db:
        result = db.execute(
            "DELETE FROM users "
            "WHERE rowid = ? "
            "RETURNING *;",
            (user_id, ),
        )
        db.commit()
    return result.fetchone()
