import sqlite3
from typing import Any

from src.repositories.exceptions import NoEntry
from src.schemas import Comment, User
from .base import SqliteRepositoryBase
from ..exceptions import FetchingError
from ...comment_classifier import comment_queue
from ...types import SQLiteExecutable


def comment_factory(cursor: SQLiteExecutable, row: tuple[Any, ...]) -> Comment:
    kw = {
        column[0]: row[idx]
        for idx, column in enumerate(cursor.description)
    }
    if 'email' not in kw or 'user_id' not in kw:
        raise FetchingError('User entry has to be fetched alongside with post entry by joining them')
    kw['author'] = User(**kw)
    comment = Comment(**kw)
    return comment


class SqliteCommentRepository(SqliteRepositoryBase):
    def get(self, comment_id: int) -> Comment:
        with self.db(row_factory=comment_factory) as db:
            cursor = db.execute(
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
            if comment := cursor.fetchone():
                return comment
            raise NoEntry()

    def get_by_author(self, user_id) -> list[Comment]:
        with self.db(row_factory=comment_factory) as db:
            cursor = db.execute(
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
                "WHERE u.rowid = ?;",
                (user_id, )
            )
            return cursor.fetchall()

    def get_by_post(self, post_id: int) -> list[Comment]:
        with self.db(row_factory=comment_factory) as db:
            cursor = db.execute(
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
            return cursor.fetchall()

    def save(self, comment: Comment) -> Comment:
        handler = self._new_comment if comment.comment_id is None else self._edit_comment
        saved_comment = handler(comment)
        comment_queue.put((saved_comment.comment_id, saved_comment.body))
        return saved_comment

    def delete(self, comment_id: int) -> Comment:
        ...

    def has_replies(self, comment_id: int) -> bool:
        with self.db() as db:
            cursor = db.execute(
                "SELECT COUNT(*) FROM comments WHERE reply_to = ?;",
                (comment_id, )
            )
            return True if cursor.fetchone()[0] != 0 else False

    def _new_comment(self, comment: Comment) -> Comment:
        with self.db() as db:
            cursor = db.execute(
                "INSERT INTO comments (reply_to, author_id, post_id, body, autoreply_at) "
                "VALUES (:reply_to, :author_id, :post_id, :body, :autoreply_at) "
                "RETURNING current_timestamp, status",
                comment.model_dump()
            )
            if row := cursor.fetchone():
                comment.comment_id = cursor.lastrowid
                comment.created_at = comment.updated_at = row[0]
                comment.status = row[1]
                db.commit()
                return comment
            raise sqlite3.DatabaseError()

    def _edit_comment(self, comment: Comment) -> Comment:
        with self.db() as db:
            cursor = db.execute(
                "UPDATE comments "
                "SET "
                "   body = ?, "
                "   status = ?, "
                "   autoreply_at = ? "
                "WHERE rowid = ? "
                "RETURNING current_timestamp, status;",
                (
                    comment.body,
                    comment.status,
                    comment.autoreply_at,
                    comment.comment_id
                )
            )
            if row := cursor.fetchone():
                comment.updated_at, comment.status = row
                db.commit()
                return comment
            raise NoEntry()
