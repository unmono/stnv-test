from typing import Annotated

from fastapi import APIRouter, Depends

from ..exceptions import not_found
from ..schemas import User, UserSettings
from ..dependencies import requesting_user

from ..repositories.protocols import UserRepository
from ..repositories.exceptions import NoEntry
from ..repositories import SqliteUserRepository


users_router = APIRouter(
    prefix='/user',
)


@users_router.get("/me/")
def user_space(
        user: Annotated[User, Depends(requesting_user)],
) -> User:
    return user


@users_router.patch("/me/")
def update_my_settings(
        user: Annotated[User, Depends(requesting_user)],
        user_settings: UserSettings,
        user_repo: Annotated[UserRepository, Depends(SqliteUserRepository)]
) -> User:
    user = user.model_copy(update=user_settings.model_dump(exclude_unset=True))
    try:
        return user_repo.save(user)
    except NoEntry:
        raise not_found
