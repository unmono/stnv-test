from ..exceptions import NoSuchUser
from ..db import sqlite_db

def get_user_credentials(
        email: str,
) -> tuple[int, str]:
    with sqlite_db() as db:
        result = db.execute(
            "SELECT rowid as id, hash "
            "FROM users "
            "WHERE email = ? "
            "LIMIT 1;",
            (email, )
        )
        if id_and_hash := result.fetchone():
            return id_and_hash
        raise NoSuchUser()