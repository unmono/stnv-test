from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.responses import RedirectResponse

from ..repositories import SqlitePostRepository
from ..repositories.exceptions import NoEntry
from ..repositories.protocols import PostRepository

from ..exceptions import internal_error, not_found, unauthorized, forbidden
from ..schemas import PostData, Post, User
from ..dependencies import requesting_user

posts_router = APIRouter(
    prefix='/posts',
)


@posts_router.get('/')
def all_posts(
        post_repo: Annotated[PostRepository, Depends(SqlitePostRepository)],
) -> list[Post]:
    return post_repo.all()


@posts_router.post('/')
def new_post(
        user: Annotated[User, Depends(requesting_user)],
        post_repo: Annotated[PostRepository, Depends(SqlitePostRepository)],
        post_data: PostData,
) -> RedirectResponse:
    post = Post(
        author=user,
        author_id=user.user_id,
        title=post_data.title,
        body=post_data.body,
    )
    try:
        saved_post = post_repo.save(post)
        return RedirectResponse(
            url=posts_router.url_path_for('get_post', post_id=saved_post.post_id),
            status_code=303,
        )
    except ValueError:
        raise internal_error

@posts_router.get('/{post_id}/')
def get_post(
        post_id: int,
        post_repo: Annotated[PostRepository, Depends(SqlitePostRepository)],
) -> Post:
    try:
        return post_repo.get(post_id)
    except NoEntry:
        raise not_found

@posts_router.patch('/{post_id}/')
def edit_post(
        user: Annotated[User, Depends(requesting_user)],
        post_repo: Annotated[PostRepository, Depends(SqlitePostRepository)],
        post_id: int,
        post_data: PostData,
) -> RedirectResponse:
    try:
        original_post = post_repo.get(post_id)
    except NoEntry:
        raise not_found
    if user.user_id != original_post.author_id:
        raise forbidden
    edited_post = original_post.model_copy(update=post_data.model_dump())
    try:
        saved_post = post_repo.save(edited_post)
        return RedirectResponse(
            url=posts_router.url_path_for('get_post', post_id=saved_post.post_id),
            status_code=303,
        )
    except NoEntry:
        raise not_found
