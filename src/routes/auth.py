from typing import Annotated
from datetime import datetime, timedelta
import jwt

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from ..repositories.protocols import AuthRepository
from ..repositories.exceptions import NoEntry, AlreadyExists
from ..repositories import SqliteAuthRepository

from ..schemas import TokenResponse, UserData
from ..exceptions import bad_credentials, internal_error
from ..settings import Settings, get_settings

auth_router = APIRouter(
    prefix='/auth',
)


@auth_router.post('/token')
def get_auth_token(
        settings: Annotated[Settings, Depends(get_settings)],
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        auth_repo: Annotated[AuthRepository, Depends(SqliteAuthRepository)]
) -> TokenResponse:
    try:
        user_id, hashed_password = auth_repo.get_user_credentials(form_data.username)
    except NoEntry:
        raise bad_credentials
    argon_ph = PasswordHasher()
    try:
        argon_ph.verify(hashed_password, form_data.password)
    except VerifyMismatchError:
        raise bad_credentials
    except (VerificationError, InvalidHashError):
        # logger.critical("Error in verifying password. Check password flow.")
        raise internal_error
    token_data = {
        'sub': user_id,
        'exp': datetime.now() + timedelta(minutes=30)
    }
    user_jwt = jwt.encode(
        token_data,
        settings.secret_key,
        algorithm='HS256',
    )
    return TokenResponse(token_type='bearer', access_token=user_jwt)


@auth_router.post('/register')
def register_new_user(
        user_data: UserData,
        auth_repo: Annotated[AuthRepository, Depends(SqliteAuthRepository)]
):
    ph = PasswordHasher()
    hashed_password = ph.hash(user_data.password)
    try:
        auth_repo.register_user(user_data.email, hashed_password)
        return {
            'detail': 'Successful registration! You can use now your credentials to get a token.'
        }
    except AlreadyExists:
        raise HTTPException(status_code=400, detail='This email has already been used')
