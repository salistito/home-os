from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from core.utils.date import get_today, month_key, to_db_date
from modules.tasks.service import (
    get_month_points,
    get_daily_points,
    get_daily_task_breakdown,
    get_day_board,
)
from modules.users.repository import get_users


async def monthly_ranking(request: Request) -> Response:
    user_names_by_id = {u.id: u.name for u in get_users()}
    month = month_key(get_today())
    month_points = get_month_points(month)
    ranking = sorted(
        (
            {
                "user_id": user_id,
                "name": user_names_by_id.get(user_id, user_id),
                "points": points,
            }
            for user_id, points in month_points.items()
        ),
        key=lambda entry: entry["points"],
        reverse=True,
    )
    return JSONResponse({"month": month, "ranking": ranking})


async def daily_breakdown(request: Request) -> Response:
    users = [{"id": u.id, "name": u.name} for u in get_users()]
    month = month_key(get_today())
    return JSONResponse(
        {
            "users": users,
            "month": month,
            "daily": get_daily_points(month),
            "tasks": get_daily_task_breakdown(month),
        }
    )


async def today_board(request: Request) -> Response:
    today = get_today()
    today_board = get_day_board(today)
    users = [
        {"id": user.id, "name": user.name, "tasks": today_board.get(user.id, [])}
        for user in get_users()
    ]
    return JSONResponse({"date": to_db_date(today), "users": users})
