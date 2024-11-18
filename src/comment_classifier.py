from queue import SimpleQueue
from threading import Thread
from typing import Callable
from contextlib import asynccontextmanager
from functools import partial

from fastapi import FastAPI
from transformers import pipeline

from .types import SQLiteExecutable
from .schemas import CommentStatus
from .db import initialize_db


def comment_modifier(
        comment_id: int,
        approve: bool,
        db: SQLiteExecutable,
) -> None:
    new_status = CommentStatus.APPROVED if approve else CommentStatus.REJECTED
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


@asynccontextmanager
async def app_setup(app: FastAPI):
    db = initialize_db(check_same_thread=False)
    callback = partial(comment_modifier, db=db)
    Thread(
        target=classifier_worker,
        daemon=True,
        kwargs={
            'callback': callback,
            'q': comment_queue,
            'model_name': "badmatr11x/distilroberta-base-offensive-hateful-speech-text-multiclassification",
        }
    ).start()

    yield

    db.close()
