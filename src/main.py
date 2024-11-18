from fastapi import FastAPI

from .comment_classifier import app_setup
from .routes import auth_router, users_router, comments_router, posts_router

app = FastAPI(lifespan=app_setup)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(posts_router)
app.include_router(comments_router)
