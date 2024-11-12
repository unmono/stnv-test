from typing import Annotated

import jwt

from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

from .repositories.protocols import UserRepository
from .repositories.exceptions import NoEntry
from .repositories import SqliteUserRepository
from .schemas import User
from .settings import Settings, get_settings

oauth_flow = OAuth2PasswordBearer(
    tokenUrl='/auth/token',
)


def requesting_user(
        settings: Annotated[Settings, Depends(get_settings)],
        token: Annotated[str, Depends(oauth_flow)],
        user_repo: Annotated[UserRepository, Depends(SqliteUserRepository)],
) -> User:
    # todo: check for guest user
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=['HS256'])
    except jwt.ExpiredSignatureError as err:
        # todo: refresh token
        raise err
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail='Invalid credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    user_id: int = payload.get('sub')
    try:
        return user_repo.get(user_id)
    except NoEntry:
        raise HTTPException(
            status_code=401,
            detail='Invalid credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )
