from typing import Annotated

import jwt

from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

from .schemas import User
from .exceptions import NoSuchUser
from .repositories import user as user_repo


oauth_flow = OAuth2PasswordBearer(
    tokenUrl='login',
)


def requesting_user(
        token: Annotated[str, Depends(oauth_flow)],
) -> User:
    # todo: check for guest user
    try:
        payload = jwt.decode(token, 'SECRET_KEY', algorithms=['HS256'])
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
        return user_repo.get_user(user_id)
    except NoSuchUser:
        raise HTTPException(
            status_code=401,
            detail='Invalid credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )
