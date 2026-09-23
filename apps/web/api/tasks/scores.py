from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from apps.web.api.tasks.responses import assignment_forbidden
from core.utils.date import get_today, month_key, to_db_date
from modules.breaks.service import (
    get_active_break_period_for_user,
    get_break_period_summary_by_user,
    serialize_break_period_infos,
)
from modules.tasks.service import (
    get_daily_assignments,
    get_daily_points,
    get_daily_task_breakdown,
    get_day_board,
    get_month_points,
    toggle_assignment,
)
from modules.users.repository import get_users


async def today_board(request: Request) -> Response:
    today = get_today()
    get_daily_assignments(today)
    today_board = get_day_board(today)
    users = []
    for user in get_users():
        active_break_period = get_active_break_period_for_user(user.id, today)
        users.append(
            {
                "id": user.id,
                "name": user.name,
                "tasks": today_board.get(user.id, []),
                "on_break": active_break_period is not None,
                "break_periods": serialize_break_period_infos([active_break_period]),
            }
        )
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
    users = get_users()
    users_by_id = {u.id: u.name for u in users}
    month = request.query_params.get("month", month_key(get_today()))
    month_points = get_month_points(month)
    break_period_summary = get_break_period_summary_by_user(month)
    on_break_period_user_ids = {u.id for u in users if u.id in break_period_summary}

    ranking = []
    for user_id in set(month_points) | on_break_period_user_ids:
        ranking.append(
            {
                "user_id": user_id,
                "name": users_by_id.get(user_id, user_id),
                "points": month_points.get(user_id, 0),
                "break_periods": break_period_summary.get(user_id, []),
            }
        )
    ranking.sort(key=lambda entry: entry["points"], reverse=True)
    return JSONResponse({"month": month, "ranking": ranking})
