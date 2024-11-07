from typing import Annotated
from argon2 import PasswordHasher
from datetime import datetime, timedelta
import jwt

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from .routes import user_router, posts_router, comments_router
from .schemas import TokenResponse, User
from .exceptions import NoSuchUser, bad_credentials, internal_error
from .repositories import auth as auth_repo


app = FastAPI(
    # dependencies=
)

app.include_router(user_router)
app.include_router(posts_router)
app.include_router(comments_router)


@app.post("/login")
def get_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenResponse:
    try:
        user_id, hashed_password = auth_repo.get_user_credentials(form_data.username)
    except NoSuchUser:
        raise HTTPException(
            status_code=400,
            detail=f"{form_data.username}",
        )
    argon_ph = PasswordHasher()
    if not argon_ph.verify(hashed_password, form_data.password):
        raise bad_credentials
    token_data = {
        'sub': user_id,
        'exp': datetime.now() + timedelta(minutes=30)
    }
    user_jwt = jwt.encode(
        token_data,
        'SECRET_KEY',
        algorithm='HS256',
    )
    return TokenResponse(token_type='bearer', access_token=user_jwt)
