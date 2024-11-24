import os
from queue import SimpleQueue
from typing import Callable

from transformers import pipeline

from .db import sqlite_cm
from .schemas import CommentStatus


def comment_modifier(
        comment_id: int,
        approve: bool,
        db_path: str | os.PathLike,
) -> None:
    new_status = CommentStatus.APPROVED if approve else CommentStatus.REJECTED
    with sqlite_cm(db_path) as db:
        db.execute(
            "UPDATE comments "
            "SET status = ? "
            "WHERE rowid = ?;",
            (int(new_status), comment_id)
        )
        db.commit()


def classifier_worker(
        callback: Callable,
        q: SimpleQueue,
        model_name: str,
) -> None:
    # logger.info("Classifier thread started")
    hate_detector = pipeline(
        'text-classification',
        model=model_name,
    )
    # logger.info("Model downloaded")
    while True:
        comment_id, text = q.get()
        # logger.info("Comment received")
        model_response = hate_detector(text)
        result = model_response[0]['label'] == 'NEITHER'
        callback(comment_id, result)


comment_queue = SimpleQueue()
