from typing import Annotated
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from starlette.responses import RedirectResponse

from .schemas import UserCredentials, User, Post, Comment, PostData, CommentData, CommentStatus
from .dependencies import requesting_user
from .exceptions import UserAlreadyExists, internal_error, unauthorized, NoSuchComment, not_found, NoSuchUser
from .repositories import (
    user as user_repo,
    post as post_repo,
    comment as comment_repo,
)


user_router = APIRouter(
    prefix="/user",
)


@user_router.post("/new/", response_model=User)
def new_user(
        user_credentials: UserCredentials,
) -> User:
    try:
        return user_repo.create_user(user_credentials)
    except UserAlreadyExists:
        raise HTTPException(status_code=400, detail='This email has already been used')


@user_router.get("/{user_id}/", response_model=User)
def user_space(
        user_id: int,
        user: Annotated[User, Depends(requesting_user)],
        request: Request,
) -> User | RedirectResponse:
    if user.user_id != user_id:
        return RedirectResponse(request.url_for('user_posts', user_id=user_id))
    user = user_repo.get_user(user_id)
    return user


@user_router.patch("/{user_id}/")
def update_user_settings(
        user_id: int,
        user_data: User,
        user: Annotated[User, Depends(requesting_user)],
):
    if user.user_id != user_id:
        raise HTTPException(
            status_code=401,
            detail='Unauthorized',
        )
    user_repo.save_user(user_data)
    return Response(status_code=200)


@user_router.get("/{user_id}/posts/")
def user_posts(user_id: int) -> list[Post]:
    return post_repo.get_posts_by_user_id(user_id)


@user_router.get("/{user_id}/comments/")
def user_comments(user_id: int):
    return comment_repo.get_comments_by_user(user_id)


posts_router = APIRouter(
    prefix="/posts",
)


@posts_router.get("/")
def posts_list() -> list[Post]:
    return post_repo.get_posts()


@posts_router.post("/")
def new_post(
        user: Annotated[User, Depends(requesting_user)],
        post_data: PostData,
) -> Post:
    post = Post(
        author = user,
        author_id = user.user_id,
        title = post_data.title,
        body = post_data.body,
    )
    try:
        post_repo.create_post(post)
    except:
        raise internal_error
    return post


@posts_router.get("/{post_id}/")
def get_post(post_id: int) -> Post:
    return post_repo.get_post_by_id(post_id)


@posts_router.patch("/{post_id}/")
def edit_post(
        post_id: int,
        post_data: PostData,
        user: Annotated[User, Depends(requesting_user)]
):
    original_post = post_repo.get_post_by_id(post_id)
    if user.user_id != original_post.author_id:
        raise unauthorized
    original_post.title = post_data.title
    original_post.body = post_data.body
    post_repo.edit_post(original_post)


@posts_router.delete("/{post_id}/")
def delete_post(post_id: int):
    pass


@posts_router.get("/{post_id}/comments/")
def post_comments(post_id: int):
    # TODO: check if post exists
    return comment_repo.get_comments_by_post(post_id)


@posts_router.post("/{post_id}/comments/")
def comment_post(
        post_id: int,
        user: Annotated[User, Depends(requesting_user)],
        comment_data: CommentData,
) -> Comment:
    # todo: autoreply from post user, not comment...
    if user.autoreply_timeout is not None:
        autoreply_at_dt = datetime.now() + timedelta(minutes=user.autoreply_timeout)
        autoreply_at = int(autoreply_at_dt.timestamp())
    else:
        autoreply_at = None
    comment = Comment(
        author=user,
        author_id=user.user_id,
        post_id=post_id,
        body=comment_data.body,
        status=CommentStatus.NOT_REVIEWED,
        autoreply_at=autoreply_at
    )
    try:
        comment_repo.create_comment(comment)
    except:
        raise internal_error
    return comment


comments_router = APIRouter(
    prefix="/comments",
)

@comments_router.get("/{comment_id}/")
def get_comment(comment_id: int) -> Comment:
    try:
        return comment_repo.get_comment(comment_id)
    except NoSuchComment:
        raise not_found


@comments_router.patch("/{comment_id}/")
def edit_comment(
        comment_id: int,
        user: Annotated[User, Depends(requesting_user)],
        comment_data: CommentData,
):
    try:
        original_comment = comment_repo.get_comment(comment_id)
    except NoSuchComment:
        raise not_found
    if user.user_id != original_comment.author_id:
        raise unauthorized
    if original_comment.autoreply_at is not None:
        if datetime.now().timestamp() >= original_comment.autoreply_at:
            raise HTTPException(
                status_code=406,
                detail='Comment has been replied',
            )
    original_comment.body = comment_data.body
    return comment_repo.edit_comment(original_comment)


@comments_router.delete("/{comment_id}/")
def delete_comment(comment_id: int):
    pass


@comments_router.post("/{comment_id}/reply/")
def reply_comment(
        comment_id: int,
        user: Annotated[User, Depends(requesting_user)],
        comment_data: CommentData,
):
    try:
        original_comment = comment_repo.get_comment(comment_id)
    except NoSuchComment:
        raise not_found
    new_comment = Comment(
        reply_to=comment_id,
        author=user,
        author_id=user.user_id,
        post_id=original_comment.post_id,
        body=comment_data.body,
    )
    comment_repo.create_comment(new_comment)
