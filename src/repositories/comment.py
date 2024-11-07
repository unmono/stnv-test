import sqlite3
from typing import Any

from ..db import sqlite_db
from ..schemas import Comment, User
from ..exceptions import FetchingError, NoSuchComment


def comment_factory(cursor: sqlite3.Cursor | sqlite3.Connection, row: tuple[Any, ...]) -> Comment:
    kw = {
        column[0]: row[idx]
        for idx, column in enumerate(cursor.description)
    }
    if 'email' not in kw or 'user_id' not in kw:
        raise FetchingError('User entry has to be fetched alongside with post entry by joining them')
    kw['author'] = User(**kw)
    comment = Comment(**kw)
    return comment


def create_comment(comment: Comment) -> Comment:
    with sqlite_db() as db:
        print(comment.model_dump())
        result = db.execute(
            "INSERT INTO comments (reply_to, author_id, post_id, body, autoreply_at) "
            "VALUES (:reply_to, :author_id, :post_id, :body, :autoreply_at) "
            "RETURNING current_timestamp, status",
            comment.model_dump()
        )
        if row := result.fetchone():
            comment.comment_id = result.lastrowid
            comment.created_at = comment.updated_at = row[0]
            comment.status = row[1]
            db.commit()
            return comment
        raise sqlite3.DatabaseError()


def get_comment(comment_id: int) -> Comment:
    with sqlite_db(row_factory=comment_factory) as db:
        result = db.execute(
            "SELECT "
            "   u.rowid as user_id, "
            "   u.email, "
            "   u.autoreply_timeout, "
            "   c.rowid as comment_id, "
            "   c.reply_to, "
            "   c.author_id, "
            "   c.post_id, "
            "   c.body, "
            "   c.status, "
            "   c.created_at, "
            "   c.updated_at, "
            "   c.autoreply_at "
            "FROM comments c "
            "INNER JOIN users u "
            "ON u.rowid = c.author_id "
            "WHERE c.rowid = ?"
            "LIMIT 1;",
            (comment_id, )
        )
        if comment := result.fetchone():
            return comment
        raise NoSuchComment("Such comment does not exist")


def get_comments_by_post(post_id: int) -> list[Comment]:
    with sqlite_db(row_factory=comment_factory) as db:
        result = db.execute(
            "SELECT "
            "   u.rowid as user_id, "
            "   u.email, "
            "   u.autoreply_timeout, "
            "   c.rowid as comment_id, "
            "   c.reply_to, "
            "   c.author_id, "
            "   c.post_id, "
            "   c.body, "
            "   c.status, "
            "   c.created_at, "
            "   c.updated_at, "
            "   c.autoreply_at "
            "FROM comments c "
            "INNER JOIN users u "
            "ON u.rowid = c.author_id "
            "WHERE c.post_id = ?;",
            (post_id, )
        )
        return result.fetchall()


def get_comments_by_user(user_id: int) -> list[Comment]:
    with sqlite_db(row_factory=comment_factory) as db:
        result = db.execute(
            "SELECT "
            "   u.rowid as user_id, "
            "   u.email, "
            "   u.autoreply_timeout, "
            "   c.rowid as comment_id, "
            "   c.reply_to, "
            "   c.author_id, "
            "   c.post_id, "
            "   c.body, "
            "   c.status, "
            "   c.created_at, "
            "   c.updated_at, "
            "   c.autoreply_at "
            "FROM comments c "
            "INNER JOIN users u "
            "ON u.rowid = c.author_id "
            "WHERE c.author_id = ?;",
            (user_id,)
        )
        return result.fetchall()


def edit_comment(edited_comment: Comment) -> Comment:
    with sqlite_db() as db:
        result = db.execute(
            "UPDATE comments "
            "SET "
            "   body = ?, "
            "   status = ?, "
            "   autoreply_at = ? "
            "WHERE rowid = ? "
            "RETURNING current_timestamp, status;",
            (
                edited_comment.body,
                edited_comment.status,
                edited_comment.autoreply_at,
                edited_comment.comment_id
            )
        )
        if row := result.fetchone():
            edited_comment.updated_at, edited_comment.status = row
            db.commit()
            return edited_comment
        raise NoSuchComment("Such comment does not exist")
