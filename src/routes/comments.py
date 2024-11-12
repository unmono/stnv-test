import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ..exceptions import not_found, unauthorized, forbidden
from ..repositories import SqliteCommentRepository, SqlitePostRepository
from ..repositories.exceptions import NoEntry
from ..repositories.protocols import CommentRepository, PostRepository
from ..schemas import CommentData, Comment, User
from ..dependencies import requesting_user


comments_router = APIRouter(
    prefix='/comments',
)


@comments_router.get('/by_post/{post_id}')
def get_comments_to_post(
        post_id: int,
        comment_repo: Annotated[CommentRepository, Depends(SqliteCommentRepository)],
) -> list[Comment]:
    return comment_repo.get_by_post(post_id)


@comments_router.post('/by_post/{post_id}')
def add_comment_to_post(
        comment_repo: Annotated[CommentRepository, Depends(SqliteCommentRepository)],
        post_repo: Annotated[PostRepository, Depends(SqlitePostRepository)],
        user: Annotated[User, Depends(requesting_user)],
        post_id: int,
        comment_data: CommentData
) -> Comment:
    try:
        post = post_repo.get(post_id)
    except NoEntry:
        raise not_found
    if post.author.autoreply_timeout is not None:
        autoreply_at = int(time.time()) + post.author.autoreply_timeout * 60
    else:
        autoreply_at = None
    new_comment = Comment(
        author=user,
        author_id=user.user_id,
        post_id=post_id,
        body=comment_data.body,
        autoreply_at=autoreply_at,
    )
    return comment_repo.save(new_comment)



@comments_router.get('/by_author/{author_id}')
def get_comments_by_author(
        author_id: int,
        comment_repo: Annotated[CommentRepository, Depends(SqliteCommentRepository)],
) -> list[Comment]:
    return comment_repo.get_by_author(author_id)


@comments_router.get('/{comment_id}')
def get_comment(
        comment_id: int,
        comment_repo: Annotated[CommentRepository, Depends(SqliteCommentRepository)]
) -> Comment:
    try:
        return comment_repo.get(comment_id)
    except NoEntry:
        raise not_found


@comments_router.post('/{comment_id}/reply')
def reply_to_comment(
        user: Annotated[User, Depends(requesting_user)],
        comment_repo: Annotated[CommentRepository, Depends(SqliteCommentRepository)],
        comment_id: int,
        comment_data: CommentData,
) -> Comment:
    try:
        original_comment = comment_repo.get(comment_id)
    except NoEntry:
        raise not_found
    if original_comment.reply_to is not None:
        raise HTTPException(
            status_code=400,
            detail='This comment cannot be replied'
        )
    new_comment = Comment(
        reply_to=original_comment.comment_id,
        author=user,
        author_id=user.user_id,
        post_id=original_comment.post_id,
        body=comment_data.body,
    )
    return comment_repo.save(new_comment)


@comments_router.patch('/{comment_id}/')
def edit_comment(
        user: Annotated[User, Depends(requesting_user)],
        comment_repo: Annotated[CommentRepository, Depends(SqliteCommentRepository)],
        comment_id: int,
        comment_data: CommentData,
) -> Comment:
    try:
        original_comment = comment_repo.get(comment_id)
    except NoEntry:
        raise not_found
    if user.user_id != original_comment.author_id:
        raise forbidden
    if comment_repo.has_replies(comment_id):
        raise HTTPException(
            status_code=418,
            detail="Comment is already replied"
        )
    edited_comment = original_comment.model_copy(update=comment_data.model_dump())
    try:
        return comment_repo.save(edited_comment)
    except NoEntry:
        raise not_found
