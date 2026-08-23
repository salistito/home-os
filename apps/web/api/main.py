import logging
from contextlib import asynccontextmanager

import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from apps.web.api.finances import routes as finances
from apps.web.api.fitness import routes as fitness
from apps.web.api.food import routes as food
from apps.web.api.middleware import AuthMiddleware
from apps.web.api.reminders import routes as reminders
from apps.web.api.tasks import routes as tasks
from apps.web.api.tasks import scores as tasks_scores
from apps.web.api.users import routes as users
from core.config import WEB_ALLOWED_ORIGINS, WEB_PORT
from core.db import init_db

logger = logging.getLogger(__name__)


async def api_health(request: Request) -> Response:
    return JSONResponse({"status": "ok"})


@asynccontextmanager
async def _lifespan(app: Starlette):
    init_db()
    yield


routes = [
    # Health
    Route("/api/health", api_health, methods=["GET"]),
    # Users
    Route("/api/users", users.create, methods=["POST"]),
    Route("/api/signup", users.signup, methods=["POST"]),
    Route("/api/login", users.login, methods=["POST"]),
    Route("/api/users", users.list_users, methods=["GET"]),
    Route("/api/users/{id:int}", users.update, methods=["PATCH"]),
    Route("/api/users/{id:int}", users.delete, methods=["DELETE"]),
    # Tasks
    Route("/api/tasks", tasks.create, methods=["POST"]),
    Route("/api/tasks", tasks.list_tasks, methods=["GET"]),
    Route("/api/tasks/{id:int}", tasks.update, methods=["PATCH"]),
    Route("/api/tasks/{id:int}", tasks.delete, methods=["DELETE"]),
    Route("/api/tasks/today-board", tasks_scores.today_board, methods=["GET"]),
    Route(
        "/api/tasks/today-board/{assignment_id:int}/toggle",
        tasks_scores.toggle_today_task,
        methods=["POST"],
    ),
    Route("/api/tasks/daily-breakdown", tasks_scores.daily_breakdown, methods=["GET"]),
    Route("/api/tasks/monthly-ranking", tasks_scores.monthly_ranking, methods=["GET"]),
    # Reminders
    Route("/api/reminders", reminders.create, methods=["POST"]),
    Route("/api/reminders", reminders.list_reminders, methods=["GET"]),
    Route("/api/reminders/{id:int}", reminders.update, methods=["PATCH"]),
    Route("/api/reminders/{id:int}", reminders.delete, methods=["DELETE"]),
    # Finances
    Route("/api/finances/periods", finances.create_period, methods=["POST"]),
    Route("/api/finances/periods", finances.list_periods, methods=["GET"]),
    Route(
        "/api/finances/periods/{id:int}",
        finances.get_period_detail_endpoint,
        methods=["GET"],
    ),
    Route("/api/finances/tags", finances.list_tags_endpoint, methods=["GET"]),
    Route("/api/finances/entries", finances.create_entry, methods=["POST"]),
    Route("/api/finances/entries", finances.list_entries_endpoint, methods=["GET"]),
    Route(
        "/api/finances/entries/{id:int}",
        finances.update_entry_endpoint,
        methods=["PATCH"],
    ),
    Route(
        "/api/finances/entries/{id:int}",
        finances.delete_entry_endpoint,
        methods=["DELETE"],
    ),
    Route(
        "/api/finances/entries/{id:int}/confirm",
        finances.confirm_entry_endpoint,
        methods=["POST"],
    ),
    # Food
    Route("/api/food/ingredients", food.create_ingredient_handler, methods=["POST"]),
    Route("/api/food/ingredients", food.list_ingredients_handler, methods=["GET"]),
    Route("/api/food/ingredients/search", food.search_ingredient_handler, methods=["POST"]),
    Route("/api/food/ingredients/import", food.import_ingredient_handler, methods=["POST"]),
    Route("/api/food/ingredients/{id:int}", food.get_ingredient_handler, methods=["GET"]),
    Route("/api/food/ingredients/{id:int}", food.update_ingredient_handler, methods=["PATCH"]),
    Route("/api/food/ingredients/{id:int}", food.delete_ingredient_handler, methods=["DELETE"]),
    Route("/api/food/stock", food.list_stock_handler, methods=["GET"]),
    Route("/api/food/stock/low", food.list_low_stock_handler, methods=["GET"]),
    Route("/api/food/stock/expiring", food.list_expiring_handler, methods=["GET"]),
    Route("/api/food/stock/{ingredient_id:int}", food.set_stock_handler, methods=["PATCH"]),
    Route("/api/food/purchases", food.create_purchase_handler, methods=["POST"]),
    Route("/api/food/purchases", food.list_purchases_handler, methods=["GET"]),
    Route("/api/food/purchases/{id:int}", food.delete_purchase_handler, methods=["DELETE"]),
    Route("/api/food/recipes", food.create_recipe_handler, methods=["POST"]),
    Route("/api/food/recipes", food.list_recipes_handler, methods=["GET"]),
    Route("/api/food/recipes/suggested", food.suggest_recipes_handler, methods=["GET"]),
    Route("/api/food/recipes/{id:int}", food.get_recipe_handler, methods=["GET"]),
    Route("/api/food/recipes/{id:int}", food.update_recipe_handler, methods=["PATCH"]),
    Route("/api/food/recipes/{id:int}", food.delete_recipe_handler, methods=["DELETE"]),
    Route("/api/food/recipes/{id:int}/cook", food.cook_recipe_handler, methods=["POST"]),
    Route("/api/food/cook-events", food.list_cook_events_handler, methods=["GET"]),
    Route("/api/food/meals", food.create_meal_entry_handler, methods=["POST"]),
    Route("/api/food/meals", food.list_meal_entries_handler, methods=["GET"]),
    Route("/api/food/meals/{id:int}", food.get_meal_entry_handler, methods=["GET"]),
    Route("/api/food/meals/{id:int}", food.update_meal_entry_handler, methods=["PATCH"]),
    Route("/api/food/meals/{id:int}", food.delete_meal_entry_handler, methods=["DELETE"]),
    Route("/api/food/nutrition-goals", food.get_goals_handler, methods=["GET"]),
    Route("/api/food/nutrition-goals", food.update_goals_handler, methods=["PATCH"]),
    # Fitness
    Route("/api/fitness/exercises", fitness.create_exercise_handler, methods=["POST"]),
    Route("/api/fitness/exercises", fitness.list_exercises_handler, methods=["GET"]),
    Route("/api/fitness/exercises/{id:int}", fitness.update_exercise_handler, methods=["PATCH"]),
    Route("/api/fitness/exercises/{id:int}", fitness.delete_exercise_handler, methods=["DELETE"]),
    Route("/api/fitness/exercise-entries", fitness.log_exercise_handler, methods=["POST"]),
    Route("/api/fitness/exercise-entries", fitness.list_exercise_entries_handler, methods=["GET"]),
    Route(
        "/api/fitness/exercise-entries/{id:int}",
        fitness.update_exercise_entry_handler,
        methods=["PATCH"],
    ),
    Route(
        "/api/fitness/exercise-entries/{id:int}",
        fitness.delete_exercise_entry_handler,
        methods=["DELETE"],
    ),
    Route("/api/fitness/weight", fitness.log_weight_handler, methods=["POST"]),
    Route("/api/fitness/weight", fitness.list_weight_handler, methods=["GET"]),
    Route("/api/fitness/weight/{id:int}", fitness.update_weight_handler, methods=["PATCH"]),
    Route("/api/fitness/weight/{id:int}", fitness.delete_weight_handler, methods=["DELETE"]),
    Route("/api/fitness/stats", fitness.get_stats_handler, methods=["GET"]),
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
