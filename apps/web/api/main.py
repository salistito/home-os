import logging
from contextlib import asynccontextmanager

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from apps.web.api import scores, tasks
from core.config import WEB_PORT
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
    Route("/api/health", health, methods=["GET"]),
    Route("/api/tasks", tasks.list_tasks, methods=["GET"]),
    Route("/api/tasks", tasks.create, methods=["POST"]),
    Route("/api/tasks/scores", scores.ranking, methods=["GET"]),
    Route("/api/tasks/scores/daily", scores.daily, methods=["GET"]),
    Route("/api/tasks/today", scores.today, methods=["GET"]),
    Route("/api/tasks/{id:int}", tasks.update, methods=["PATCH"]),
    Route("/api/tasks/{id:int}", tasks.delete, methods=["DELETE"]),
]

app = Starlette(routes=routes, lifespan=_lifespan)


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        level=logging.INFO,
    )
    uvicorn.run(app, host="0.0.0.0", port=WEB_PORT)


if __name__ == "__main__":
    main()
