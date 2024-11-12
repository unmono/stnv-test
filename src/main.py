from fastapi import FastAPI

from .routes import auth_router, users_router, comments_router, posts_router


app = FastAPI()
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(posts_router)
app.include_router(comments_router)
