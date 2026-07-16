import logging
import uvicorn

from contextlib import asynccontextmanager
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from apps.web.api.auth import routes as auth
from apps.web.api.middleware import AuthMiddleware
from apps.web.api.finances import routes as finances
from apps.web.api.reminders import routes as reminders
from apps.web.api.tasks import routes as tasks, scores as tasks_scores
from apps.web.api import users
from core.config import WEB_ALLOWED_ORIGINS, WEB_PORT
from core.db import init_db
from core.seed import load_seed

logger = logging.getLogger(__name__)


async def health(request: Request) -> Response:
    return JSONResponse({"status": "ok"})


@asynccontextmanager
async def _lifespan(app: Starlette):
    init_db()
    load_seed()
    yield


routes = [
    # Health
    Route("/api/health", health, methods=["GET"]),
    # Login
    Route("/api/login", auth.login, methods=["POST"]),
    # Users
    Route("/api/users", users.list_users, methods=["GET"]),
    # Tasks
    Route("/api/tasks", tasks.create, methods=["POST"]),
    Route("/api/tasks", tasks.list_tasks, methods=["GET"]),
    Route("/api/tasks/{id:int}", tasks.update, methods=["PATCH"]),
    Route("/api/tasks/{id:int}", tasks.delete, methods=["DELETE"]),
    Route("/api/tasks/scores", tasks_scores.ranking, methods=["GET"]),
    Route("/api/tasks/scores/daily", tasks_scores.daily, methods=["GET"]),
    Route("/api/tasks/today", tasks_scores.today, methods=["GET"]),
    # Reminders
    Route("/api/reminders", reminders.create, methods=["POST"]),
    Route("/api/reminders", reminders.list_reminders, methods=["GET"]),
    Route("/api/reminders/{id:int}", reminders.update, methods=["PATCH"]),
    Route("/api/reminders/{id:int}", reminders.delete, methods=["DELETE"]),
    # Finances
    Route("/api/finances/periods", finances.create_period, methods=["POST"]),
    Route("/api/finances/periods", finances.list_periods, methods=["GET"]),
    Route("/api/finances/periods/{id:int}", finances.get_period_detail, methods=["GET"]),
    Route("/api/finances/entries", finances.create_entry, methods=["POST"]),
    Route("/api/finances/entries", finances.list_entries_endpoint, methods=["GET"]),
    Route(
        "/api/finances/entries/{id:int}/confirm",
        finances.confirm_entry_endpoint,
        methods=["POST"],
    ),
    Route(
        "/api/finances/entries/{id:int}/reject",
        finances.reject_entry_endpoint,
        methods=["POST"],
    ),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=WEB_ALLOWED_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    ),
    Middleware(AuthMiddleware),
]

app = Starlette(routes=routes, middleware=middleware, lifespan=_lifespan)


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        level=logging.INFO,
    )
    uvicorn.run(app, host="0.0.0.0", port=WEB_PORT)


if __name__ == "__main__":
    main()
