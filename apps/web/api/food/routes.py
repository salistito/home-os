import json
from http import HTTPStatus

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from apps.web.api.food.responses import (
    error_response,
    serialize_cook_event,
    serialize_ingredient,
    serialize_nutrition_goals,
    serialize_purchase,
    serialize_recipe,
    serialize_recipe_summary,
    serialize_stock,
)
from apps.web.api.responses import bad_request
from modules.food.service import (
    cook_recipe,
    create_ingredient,
    create_recipe,
    delete_ingredient,
    delete_purchase,
    delete_recipe,
    get_expiring_soon,
    get_ingredient,
    get_low_stock,
    get_nutrition_goals,
    get_recipe,
    get_stock,
    import_ingredient_from_external,
    list_cook_events,
    list_ingredients,
    list_purchases,
    list_recipes,
    register_purchase,
    set_stock,
    suggest_recipes,
    update_ingredient,
    update_nutrition_goals,
    update_recipe,
)
from modules.food.types import FoodOperationStatus, GoalTarget


def _parse_request_body(data: object) -> dict | None:
    if not isinstance(data, dict):
        return None
    return data


async def create_ingredient_handler(request: Request) -> Response:
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = _parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    name = body.get("name")
    category = body.get("category")
    unit = body.get("unit")
    macros = body.get("macros")

    if not isinstance(name, str):
        return bad_request("name is required and must be a string.")
    if not isinstance(unit, str):
        return bad_request("unit is required and must be a string.")
    if not isinstance(macros, dict):
        return bad_request("macros is required and must be a JSON object.")

    result = create_ingredient(name, category, unit, macros)
    if result.status is not FoodOperationStatus.OK:
        return error_response(result.status)

    return JSONResponse(serialize_ingredient(result.ingredient), status_code=HTTPStatus.CREATED)


async def get_ingredient_handler(request: Request) -> Response:
    ingredient_id = request.path_params["id"]
    result = get_ingredient(ingredient_id)
    if result.status is not FoodOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_ingredient(result.ingredient))


async def list_ingredients_handler(request: Request) -> Response:
    category = request.query_params.get("category")
    ingredients = list_ingredients(category)
    return JSONResponse([serialize_ingredient(i) for i in ingredients])


async def update_ingredient_handler(request: Request) -> Response:
    ingredient_id = request.path_params["id"]
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = _parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    name = body.get("name")
    category = body.get("category")
    unit = body.get("unit")
    macros = body.get("macros")

    if name is not None and not isinstance(name, str):
        return bad_request("name must be a string.")
    if category is not None and not isinstance(category, str):
        return bad_request("category must be a string.")
    if unit is not None and not isinstance(unit, str):
        return bad_request("unit must be a string.")
    if macros is not None and not isinstance(macros, dict):
        return bad_request("macros must be a JSON object.")

    result = update_ingredient(
        ingredient_id, name=name, category=category, unit=unit, macros=macros
    )
    if result.status is not FoodOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_ingredient(result.ingredient))


async def delete_ingredient_handler(request: Request) -> Response:
    ingredient_id = request.path_params["id"]
    result = delete_ingredient(ingredient_id)
    if result.status is not FoodOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_ingredient(result.ingredient))


async def import_ingredient_handler(request: Request) -> Response:
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = _parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    name = body.get("name")
    if not isinstance(name, str) or not name.strip():
        return bad_request("name is required and must be a non-empty string.")

    source = body.get("source", "openfoodfacts")
    result = import_ingredient_from_external(name, source)
    if result.status is not FoodOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_ingredient(result.ingredient), status_code=HTTPStatus.CREATED)


async def set_stock_handler(request: Request) -> Response:
    ingredient_id = request.path_params["ingredient_id"]
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = _parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    quantity = body.get("quantity")
    min_alert = body.get("min_alert_quantity", 0.0)
    expiration_date = body.get("expiration_date")

    if not isinstance(quantity, (int, float)):
        return bad_request("quantity is required and must be a number.")

    result = set_stock(ingredient_id, quantity, min_alert, expiration_date)
    if result.status is not FoodOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_stock(result.stock))


async def list_stock_handler(request: Request) -> Response:
    stock = get_stock()
    return JSONResponse([serialize_stock(s) for s in stock])


async def list_low_stock_handler(request: Request) -> Response:
    stock = get_low_stock()
    return JSONResponse([serialize_stock(s) for s in stock])


async def list_expiring_handler(request: Request) -> Response:
    days_param = request.query_params.get("days", "7")
    try:
        days = int(days_param)
    except (TypeError, ValueError):
        return bad_request("days must be an integer.")
    stock = get_expiring_soon(days)
    return JSONResponse([serialize_stock(s) for s in stock])


async def create_purchase_handler(request: Request) -> Response:
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = _parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    ingredient_id = body.get("ingredient_id")
    quantity = body.get("quantity")
    price = body.get("price")
    purchased_at = body.get("purchased_at")
    notes = body.get("notes")

    if not isinstance(ingredient_id, int):
        return bad_request("ingredient_id is required and must be an integer.")
    if not isinstance(quantity, (int, float)):
        return bad_request("quantity is required and must be a number.")
    if not isinstance(price, int):
        return bad_request("price is required and must be an integer.")
    if not isinstance(purchased_at, str):
        return bad_request("purchased_at is required and must be a string.")

    result = register_purchase(ingredient_id, quantity, price, purchased_at, notes)
    if result.status is not FoodOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_purchase(result.purchase), status_code=HTTPStatus.CREATED)


async def list_purchases_handler(request: Request) -> Response:
    ingredient_id = request.query_params.get("ingredient_id")
    from_date = request.query_params.get("from_date")
    to_date = request.query_params.get("to_date")

    if ingredient_id is not None:
        try:
            ingredient_id_int = int(ingredient_id)
        except (TypeError, ValueError):
            return bad_request("ingredient_id must be an integer.")
    else:
        ingredient_id_int = None

    purchases = list_purchases(ingredient_id_int, from_date, to_date)
    return JSONResponse([serialize_purchase(p) for p in purchases])


async def delete_purchase_handler(request: Request) -> Response:
    purchase_id = request.path_params["id"]
    result = delete_purchase(purchase_id)
    if result.status is not FoodOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_purchase(result.purchase))


async def create_recipe_handler(request: Request) -> Response:
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = _parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    name = body.get("name")
    portions = body.get("portions")
    ingredients = body.get("ingredients")
    description = body.get("description")
    steps = body.get("steps")

    if not isinstance(name, str):
        return bad_request("name is required and must be a string.")
    if not isinstance(portions, int) or isinstance(portions, bool):
        return bad_request("portions is required and must be an integer.")
    if not isinstance(ingredients, list):
        return bad_request("ingredients is required and must be a list.")

    result = create_recipe(name, portions, ingredients, description, steps)
    if result.status is not FoodOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_recipe(result.recipe), status_code=HTTPStatus.CREATED)


async def get_recipe_handler(request: Request) -> Response:
    recipe_id = request.path_params["id"]
    result = get_recipe(recipe_id)
    if result.status is not FoodOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_recipe(result.recipe))


async def list_recipes_handler(request: Request) -> Response:
    ingredient_ids_raw = request.query_params.get("ingredient_ids")
    ingredient_ids = None
    if ingredient_ids_raw is not None:
        try:
            ingredient_ids = [int(x.strip()) for x in ingredient_ids_raw.split(",") if x.strip()]
        except (TypeError, ValueError):
            return bad_request("ingredient_ids must be a comma-separated list of integers.")
    recipes = list_recipes(ingredient_ids)
    return JSONResponse([serialize_recipe(r) for r in recipes])


async def suggest_recipes_handler(request: Request) -> Response:
    limit_param = request.query_params.get("limit", "3")
    try:
        limit = int(limit_param)
    except (TypeError, ValueError):
        return bad_request("limit must be an integer.")

    only_with_stock_raw = request.query_params.get("only_with_stock", "true")
    only_with_stock = only_with_stock_raw.lower() in ("true", "1")

    goal_target = None
    target_macros = {
        "kcal_target": None,
        "protein_g_target": None,
        "carbs_g_target": None,
        "fat_g_target": None,
    }
    for macro in target_macros:
        val = request.query_params.get(macro)
        if val is not None:
            try:
                target_macros[macro] = float(val) if "_g_" in macro else int(val)
            except (TypeError, ValueError):
                return bad_request(f"{macro} must be a number.")

    if any(v is not None for v in target_macros.values()):
        goal_target = GoalTarget(**target_macros)

    variety_days_raw = request.query_params.get("variety_days", "0")
    try:
        variety_days = int(variety_days_raw)
    except (TypeError, ValueError):
        return bad_request("variety_days must be an integer.")

    result = suggest_recipes(
        user_id=request.state.user_id,
        limit=limit,
        only_with_stock=only_with_stock,
        goal_target=goal_target,
        variety_days=variety_days,
    )
    return JSONResponse([serialize_recipe_summary(rs) for rs in result.recipes])


async def update_recipe_handler(request: Request) -> Response:
    recipe_id = request.path_params["id"]
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = _parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    name = body.get("name")
    portions = body.get("portions")
    description = body.get("description")
    steps = body.get("steps")
    ingredients = body.get("ingredients")

    if name is not None and not isinstance(name, str):
        return bad_request("name must be a string.")
    if portions is not None and (not isinstance(portions, int) or isinstance(portions, bool)):
        return bad_request("portions must be an integer.")
    if ingredients is not None and not isinstance(ingredients, list):
        return bad_request("ingredients must be a list.")

    result = update_recipe(
        recipe_id,
        name=name,
        portions=portions,
        description=description,
        steps=steps,
        ingredients=ingredients,
    )
    if result.status is not FoodOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_recipe(result.recipe))


async def delete_recipe_handler(request: Request) -> Response:
    recipe_id = request.path_params["id"]
    result = delete_recipe(recipe_id)
    if result.status is not FoodOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_recipe(result.recipe))


async def cook_recipe_handler(request: Request) -> Response:
    recipe_id = request.path_params["id"]
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = _parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    portions = body.get("portions")
    cooked_at = body.get("cooked_at")

    if not isinstance(portions, int) or isinstance(portions, bool):
        return bad_request("portions is required and must be an integer.")

    result = cook_recipe(recipe_id, portions, cooked_at)
    if result.status is not FoodOperationStatus.OK:
        return JSONResponse(
            {"error": result.status.value, "missing_ingredient_ids": result.missing_ingredient_ids},
            status_code=HTTPStatus.CONFLICT,
        )
    return JSONResponse(
        {
            "cook_event": serialize_cook_event(result.cook_event),
            "macros": {
                "total": result.macros.total,
                "per_portion": result.macros.per_portion,
            },
        },
        status_code=HTTPStatus.CREATED,
    )


async def list_cook_events_handler(request: Request) -> Response:
    recipe_id = request.query_params.get("recipe_id")
    from_date = request.query_params.get("from_date")
    to_date = request.query_params.get("to_date")

    if recipe_id is not None:
        try:
            recipe_id_int = int(recipe_id)
        except (TypeError, ValueError):
            return bad_request("recipe_id must be an integer.")
    else:
        recipe_id_int = None

    events = list_cook_events(recipe_id_int, from_date, to_date)
    return JSONResponse([serialize_cook_event(e) for e in events])


async def get_goals_handler(request: Request) -> Response:
    user_id = request.state.user_id
    result = get_nutrition_goals(user_id)
    if result.status is not FoodOperationStatus.OK:
        return JSONResponse(
            {
                "kcal_target": None,
                "protein_g_target": None,
                "carbs_g_target": None,
                "fat_g_target": None,
                "updated_at": None,
            }
        )
    return JSONResponse(serialize_nutrition_goals(result.goals))


async def update_goals_handler(request: Request) -> Response:
    user_id = request.state.user_id
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = _parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    kwargs: dict = {}
    for key in ("kcal_target", "protein_g_target", "carbs_g_target", "fat_g_target"):
        if key in body:
            kwargs[key] = body[key]

    if not kwargs:
        return bad_request("At least one target field must be provided.")

    result = update_nutrition_goals(user_id=user_id, **kwargs)
    if result.status is not FoodOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_nutrition_goals(result.goals))
