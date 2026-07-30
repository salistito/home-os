from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from apps.web.api.tasks.responses import assignment_forbidden
from core.utils.date import get_today, month_key, to_db_date
from modules.tasks.service import (
    get_daily_points,
    get_daily_task_breakdown,
    get_day_board,
    get_month_points,
    toggle_assignment,
)
from modules.users.repository import get_users


async def today_board(request: Request) -> Response:
    today = get_today()
    today_board = get_day_board(today)
    users = [
        {"id": user.id, "name": user.name, "tasks": today_board.get(user.id, [])}
        for user in get_users()
    ]
    return JSONResponse({"date": to_db_date(today), "users": users})


async def toggle_today_task(request: Request) -> Response:
    assignment_id = request.path_params["assignment_id"]
    user_id = request.state.user_id

    result = toggle_assignment(assignment_id, user_id)
    if result is None:
        return assignment_forbidden()

    return JSONResponse({"done": result["done"]})


async def daily_breakdown(request: Request) -> Response:
    users = [{"id": u.id, "name": u.name} for u in get_users()]
    month = request.query_params.get("month", month_key(get_today()))
    return JSONResponse(
        {
            "users": users,
            "month": month,
            "daily": get_daily_points(month),
            "tasks": get_daily_task_breakdown(month),
        }
    )


async def monthly_ranking(request: Request) -> Response:
    user_names_by_id = {u.id: u.name for u in get_users()}
    month = request.query_params.get("month", month_key(get_today()))
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
