import sqlite3
from typing import Any

from src.schemas import Post, User
from src.types import SqliteExecutable
from ..exceptions import NoEntry, FetchingError
from .base import SqliteRepositoryBase


def post_factory(cursor: SqliteExecutable, row: tuple[Any, ...]) -> Post:
    kw = {
        column[0]: row[idx]
        for idx, column in enumerate(cursor.description)
    }
    if 'email' not in kw or 'user_id' not in kw:
        raise FetchingError('User entry has to be fetched alongside with post entry by joining them')
    kw['author'] = User(**kw)
    post = Post(**kw)
    return post


class SqlitePostRepository(SqliteRepositoryBase):
    def _setup(self):
        self.row_factory = post_factory

    def all(self) -> list[Post]:
        with self.db(row_factory=post_factory) as db:
            cursor = db.execute(
                "SELECT "
                "   u.rowid as user_id, "
                "   u.email, "
                "   u.autoreply_timeout, "
                "   p.rowid as post_id, "
                "   p.author_id, "
                "   p.title, "
                "   p.body, "
                "   p.created_at, "
                "   p.updated_at "
                "FROM posts p "
                "INNER JOIN users u "
                "ON p.author_id = u.rowid "
                "ORDER BY created_at DESC;"
            )
            return cursor.fetchall()

    def get(self, post_id: int) -> Post:
        with self.db(row_factory=post_factory) as db:
            cursor = db.execute(
                "SELECT "
                "   u.rowid as user_id, "
                "   u.email, "
                "   u.autoreply_timeout, "
                "   p.rowid as post_id, "
                "   p.author_id, "
                "   p.title, "
                "   p.body, "
                "   p.created_at, "
                "   p.updated_at "
                "FROM posts p "
                "INNER JOIN users u "
                "ON p.author_id = u.rowid "
                "WHERE p.rowid = ?"
                "LIMIT 1;",
                (post_id,),
            )
            if post := cursor.fetchone():
                return post
            raise NoEntry

    def get_by_author(self, user_id: int) -> list[Post]:
        with self.db(row_factory=post_factory) as db:
            cursor = db.execute(
                "SELECT "
                "   u.rowid as user_id, "
                "   u.email, "
                "   u.autoreply_timeout, "
                "   p.rowid as post_id, "
                "   p.author_id, "
                "   p.title, "
                "   p.body, "
                "   p.created_at, "
                "   p.updated_at "
                "FROM posts p "
                "INNER JOIN users u "
                "ON p.author_id = u.rowid "
                "WHERE p.author_id = ?;",
                (user_id,),
            )
            return cursor.fetchall()

    def save(self, post: Post) -> Post:
        handler = self._new_post if post.post_id is None else self._edit_post
        return handler(post)

    def delete(self, post_id: int) -> Post:
        ...

    def _new_post(self, post: Post) -> Post:
        if post.author is None:
            raise ValueError("Post object must contain author instance")
        with self.db() as db:
            result: sqlite3.Cursor = db.execute(
                "INSERT INTO posts (author_id, title, body) "
                "VALUES(?, ?, ?) "
                "RETURNING created_at, updated_at;",
                (post.author_id, post.title, post.body),
            )
            post.post_id = result.lastrowid
            post.created_at, post.updated_at = result.fetchone()
            db.commit()
        return post

    def _edit_post(self, post: Post) -> Post:
        with self.db() as db:
            result = db.execute(
                "UPDATE posts "
                "SET "
                "   title = ?, "
                "   body = ? "
                "WHERE rowid = ? "
                "RETURNING current_timestamp;",
                (post.title, post.body, post.post_id),
            )
            if row := result.fetchone():
                post.updated_at, = row
                db.commit()
                return post
            raise NoEntry("Such post does not exist")
