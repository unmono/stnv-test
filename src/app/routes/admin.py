from typing import Annotated
from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from ..repositories import SqliteCommentRepository
from ..repositories.protocols import CommentRepository
from ..schemas import User, CommentStatus
from ..dependencies import requesting_user

admin_router = APIRouter(
    prefix='/admin',
)


@admin_router.get('/comments-daily-breakdown/')
def comments_statistic(
        date_from: str,
        date_to: str,
        user: Annotated[User, Depends(requesting_user)],
        comment_repo: Annotated[CommentRepository, Depends(SqliteCommentRepository)],
):
    try:
        date.fromisoformat(date_from)
        date.fromisoformat(date_to)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail='Use YYYY-MM-DD as date format',
        )
    stats = comment_repo.get_stats_by_date(date_from, date_to)
    result = []
    current_day = None
    for stat in stats:
        if current_day != stat[0]:
            current_day = stat[0]
            result.append({
                'date': current_day,
            })
        status = CommentStatus(stat[1])
        result[-1][status.name.lower()] = stat[2]
    return result
