from datetime import datetime, timedelta
from enum import IntEnum
from typing import Annotated

from pydantic import BaseModel, EmailStr, SecretStr, AfterValidator, Field


def validate_password(v: SecretStr) -> str:
    pwd = v.get_secret_value()
    assert 8 <= len(v) <= 32, 'Password must be from 8 to 32 characters long'
    checklist: list[str | None] = ['number', 'uppercase letter', 'lowercase letter', 'special character']
    for c in pwd:
        ac = ord(c)  # ASCII code
        match ac:
            case ac if 48 <= ac <= 57:
                checklist[0] = None
            case ac if 65 <= ac <= 90:
                checklist[1] = None
            case ac if 97 <= ac <= 122:
                checklist[2] = None
            case ac if 21 <= ac <= 126:
                checklist[3] = None
            case _:
                raise ValueError(
                    f'You can use only these symbols for password: {' '.join([chr(i) for i in range(21, 127)])}'
                )
    unchecked = [c_type for c_type in checklist if c_type is not None]
    if unchecked:
        raise ValueError(
            f'To strengthen your password add {', '.join(unchecked)}'
        )
    return pwd


PasswordField = Annotated[SecretStr, AfterValidator(validate_password)]


class UserCredentials(BaseModel):
    email: EmailStr
    password: PasswordField


class User(BaseModel):
    user_id: int
    email: EmailStr
    autoreply_timeout: int | None = Field(default=None, ge=-1, le=24 * 60 * 60)


class TokenResponse(BaseModel):
    token_type: str
    access_token: str


class PostData(BaseModel):
    title: str
    body: str


class Post(BaseModel):
    post_id: int | None = None
    author: User
    author_id: int
    title: str
    body: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CommentData(BaseModel):
    body: str


class CommentStatus(IntEnum):
    NOT_REVIEWED = 0
    APPROVED = 1
    REJECTED = 2


class Comment(BaseModel):
    comment_id: int | None = None
    reply_to: int | None = None
    author: User | None = None
    author_id: int
    # post: Post | None = None
    post_id: int
    body: str
    status: CommentStatus = CommentStatus.NOT_REVIEWED
    created_at: datetime | None = None
    updated_at: datetime | None = None
    autoreply_at: int | None = None
