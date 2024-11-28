import sqlite3
import time
from typing import Any

from .base import SqliteRepositoryBase
from ..exceptions import FetchingError, NoEntry
from ...comment_classifier import comment_queue
from ...types import SQLiteExecutable, CommentsAutoreplyData
from ...schemas import Comment, CommentInfo, User


def comment_factory(cursor: SQLiteExecutable, row: tuple[Any, ...]) -> CommentInfo:
    kw = {
        column[0]: row[idx]
        for idx, column in enumerate(cursor.description)
    }
    if 'email' not in kw or 'user_id' not in kw:
        raise FetchingError('User entry has to be fetched alongside with post entry by joining them')
    kw['author'] = User(**kw)
    comment = CommentInfo(**kw)
    return comment


class SqliteCommentRepository(SqliteRepositoryBase):
    def get(self, comment_id: int) -> CommentInfo:
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
                "WHERE c.rowid = ? "
                "LIMIT 1;",
                (comment_id, )
            )
            if comment := cursor.fetchone():
                return comment
            raise NoEntry()

    def get_by_author(self, user_id) -> list[CommentInfo]:
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

    def get_by_post(self, post_id: int) -> list[CommentInfo]:
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
                "WHERE c.post_id = ? AND c.status = 1;",
                (post_id, )
            )
            return cursor.fetchall()

    def get_stats_by_date(self, date_from: str, date_to: str):
        with self.db() as db:
            cursor = db.execute(
                "SELECT date(created_at) as day, status, COUNT(*) "
                "FROM comments "
                "WHERE day >= ? AND day <= ? "
                "GROUP BY status, day "
                "ORDER BY day;",
                (date_from, date_to)
            )
            return cursor.fetchall()

    def save(self, comment: Comment) -> Comment:
        handler = self._new_comment if comment.comment_id is None else self._edit_comment
        saved_comment = handler(comment)
        comment_queue.put((saved_comment.comment_id, saved_comment.body))
        return saved_comment

    def delete(self, comment_id: int) -> CommentInfo:
        ...

    def has_replies(self, comment_id: int) -> bool:
        with self.db() as db:
            cursor = db.execute(
                "SELECT COUNT(*) FROM comments WHERE reply_to = ?;",
                (comment_id, )
            )
            return True if cursor.fetchone()[0] != 0 else False

    def get_comments_to_reply(self) -> CommentsAutoreplyData:
        with self.db() as db:
            cursor = db.execute(
                "SELECT "
                "   c.rowid as comment_id, "
                "   c.body as text, "
                "   c.post_id as post_id, "
                "   p.author_id as post_author_id "
                "FROM comments c "
                "INNER JOIN posts p "
                "ON c.post_id = p.rowid "
                "WHERE c.status = 1 "
                "   AND c.reply_to IS NULL "
                "   AND c.author_id <> p.author_id"
                "   AND c.autoreply_at < ?;",
                (time.time(), )
            )
            return cursor.fetchall()

    def post_autoreply(self, comment_id: int, reply_text: str, post_id, post_author_id: int) -> None:
        with self.db() as db:
            cursor = db.execute(
                "UPDATE comments "
                "SET autoreply_at = NULL "
                "WHERE rowid = ?;",
                (comment_id, )
            )
            cursor.execute(
                "INSERT INTO comments (author_id, reply_to, post_id, body) "
                "VALUES (?, ?, ?, ?);",
                (post_author_id, comment_id, post_id, reply_text)
            )
            comment_queue.put((cursor.lastrowid, reply_text))
            db.commit()

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
