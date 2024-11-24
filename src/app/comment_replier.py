import asyncio

from .db import prepare_db
from .exceptions import NotConfiguredError
from .repositories import SqliteCommentRepository
from .repositories.protocols import CommentRepository
from .settings import Settings


async def get_gemini_reply(api_key: str, text: str) -> str:
    if api_key is None:
        raise NotConfiguredError('Missing google api key in settings')
    return text + ' [modified]'


async def autoreply_procedure(
        api_key: str,
        comment_id: int,
        text: str,
        post_id: int,
        post_author_id: int,
        repo: CommentRepository,
):
    reply_text = await get_gemini_reply(api_key, text)
    repo.post_autoreply(
        comment_id,
        reply_text,
        post_id,
        post_author_id
    )


async def replier_worker(settings: Settings):
    comment_repo = SqliteCommentRepository(db=prepare_db(settings))
    while True:
        await asyncio.sleep(30)
        # logger.info('Checking comments')
        pending_comments_data = comment_repo.get_comments_to_reply()
        tasks = [
            asyncio.create_task(
                autoreply_procedure(
                    settings.google_key,
                    comment_id, text,
                    post_id,
                    post_author_id,
                    comment_repo,
                )
            )
            for comment_id, text, post_id, post_author_id
            in pending_comments_data
        ]
        # logger.info(f'{len(tasks)} comments to reply')
        await asyncio.gather(*tasks)
        # logger.info('Replying finished')
