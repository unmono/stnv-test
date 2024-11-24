import asyncio
from contextlib import asynccontextmanager
from functools import partial
from threading import Thread

from fastapi import FastAPI

from .comment_classifier import comment_modifier, classifier_worker, comment_queue
from .comment_replier import replier_worker
from .routes import auth_router, users_router, comments_router, posts_router
from .db import initialize_db
from .settings import get_settings


@asynccontextmanager
async def app_setup(app: FastAPI):
    settings = get_settings()
    initialize_db(settings)
    callback = partial(comment_modifier, db_path=settings.db_path)
    Thread(
        target=classifier_worker,
        daemon=True,
        kwargs={
            'callback': callback,
            'q': comment_queue,
            'model_name': "badmatr11x/distilroberta-base-offensive-hateful-speech-text-multiclassification",
        }
    ).start()
    asyncio.create_task(replier_worker(settings))
    yield


app = FastAPI(lifespan=app_setup)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(posts_router)
app.include_router(comments_router)
