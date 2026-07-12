from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from core.identity import get_users
from core.utils.date import get_today, month_key, to_db_date
from modules.tasks.service import (
    get_daily_balance,
    get_day_board,
    get_month_balance,
)


async def ranking(request: Request) -> Response:
    month = month_key(get_today())
    balance = get_month_balance(month)
    names = {u.id: u.name for u in get_users()}
    entries = sorted(
        (
            {"user_id": user_id, "name": names.get(user_id, user_id), "points": points}
            for user_id, points in balance.items()
        ),
        key=lambda entry: entry["points"],
        reverse=True,
    )
    return JSONResponse({"month": month, "ranking": entries})


async def daily(request: Request) -> Response:
    month = month_key(get_today())
    users = [{"id": u.id, "name": u.name} for u in get_users()]
    return JSONResponse(
        {"month": month, "users": users, "daily": get_daily_balance(month)}
    )


async def today(request: Request) -> Response:
    day = get_today()
    board = get_day_board(day)
    users = [
        {
            "id": user.id,
            "name": user.name,
            "tasks": [
                {"task_id": a.task_id, "name": a.task_name, "points": a.points}
                for a in board.get(user.id, [])
            ],
            "total": sum(a.points for a in board.get(user.id, [])),
        }
        for user in get_users()
    ]
    return JSONResponse({"date": to_db_date(day), "users": users})
