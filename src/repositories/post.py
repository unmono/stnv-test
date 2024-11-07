import sqlite3
from typing import Any

from ..db import sqlite_db
from ..schemas import Post, User
from ..exceptions import FetchingError, NoSuchPost


def post_factory(cursor: sqlite3.Cursor | sqlite3.Connection, row: tuple[Any, ...]) -> Post:
    # TODO: convert timestamps to datetime objects
    kw = {
        column[0]: row[idx]
        for idx, column in enumerate(cursor.description)
    }
    if 'email' not in kw or 'user_id' not in kw:
        raise FetchingError('User entry has to be fetched alongside with post entry by joining them')
    kw['author'] = User(**kw)
    post = Post(**kw)
    return post


def create_post(new_post: Post) -> Post:
    if new_post.author is None:
        raise ValueError("Post object must contain author instance")
    with sqlite_db() as db:
        result = db.execute(
            "INSERT INTO posts (author_id, title, body) "
            "VALUES(?, ?, ?) "
            "RETURNING created_at, updated_at;",
            (new_post.author_id, new_post.title, new_post.body),
        )
        new_post.created_at, new_post.updated_at = result.fetchone()
        db.commit()
    return new_post


def get_posts() -> list[Post]:
    with sqlite_db(row_factory=post_factory) as db:
        posts_cursor = db.execute(
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
        return posts_cursor.fetchall()


def get_post_by_id(post_id: int) -> Post:
    with sqlite_db(row_factory=post_factory) as db:
        posts_cursor = db.execute(
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
            (post_id, ),
        )
        if post := posts_cursor.fetchone():
            return post
        raise NoSuchPost


def get_posts_by_user_id(user_id: int) -> list[Post]:
    with sqlite_db(row_factory=post_factory) as db:
        posts_cursor = db.execute(
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
            (user_id, ),
        )
        return posts_cursor.fetchall()


def edit_post(edited_post: Post) -> Post:
    with sqlite_db() as db:
        result = db.execute(
            "UPDATE posts "
            "SET "
            "   title = ?, "
            "   body = ? "
            "WHERE rowid = ? "
            "RETURNING current_timestamp;",
            (edited_post.title, edited_post.body, edited_post.post_id),
        )
        if row := result.fetchone():
            edited_post.updated_at, = row
            db.commit()
            return edited_post
    raise NoSuchPost("Such post does not exist")
