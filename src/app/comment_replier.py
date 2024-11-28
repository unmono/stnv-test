import asyncio
import aiohttp

from .db import prepare_db
from .exceptions import NotConfiguredError
from .repositories import SqliteCommentRepository
from .repositories.protocols import CommentRepository
from .settings import Settings


async def get_gemini_reply(api_key: str, text: str) -> str:
    if api_key is None:
        raise NotConfiguredError('Missing google api key in settings')
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}'
    prompt_body = {
        'generationConfig': {
            'temperature': 1,
            'maxOutputTokens': 200,
        },
        'system_instruction': {
            'parts': {
                'text': 'You are an author of a blog post. '
                        'Every prompt you will get is a comment of different user. '
                        'Write a simple reply to this comment. Thank positive comments. '
                        'Appreciate neutral critique. '
                        'Be playful in response to negative comments.'
            },
        },
        'contents': {
            'parts': {'text': text},
        },
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=prompt_body) as response:
            assert response.status == 200
            jsn = await response.json()
            reply_text = jsn['candidates'][0]['content']['parts'][0]['text']
    return reply_text


async def autoreply_procedure(
        api_key: str,
        comment_id: int,
        text: str,
        post_id: int,
        post_author_id: int,
        repo: CommentRepository,
):
    try:
        reply_text = await get_gemini_reply(api_key, text)
    except Exception as err:
        # logger.error(f'Error in autoreplying process.\n{err}')
        pass
    else:
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
                    comment_id,
                    text,
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
