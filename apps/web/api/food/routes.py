import json
from http import HTTPStatus

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from apps.web.api.food.responses import (
    error_response,
    insufficient_stock_response,
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
    search_ingredient_from_external,
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
    purchase_unit = body.get("purchase_unit")
    purchase_conversion_factor = body.get("purchase_conversion_factor")

    if not isinstance(name, str):
        return bad_request("name is required and must be a string.")
    if not isinstance(unit, str):
        return bad_request("unit is required and must be a string.")
    if not isinstance(macros, dict):
        return bad_request("macros is required and must be a JSON object.")
    if purchase_conversion_factor is not None and not isinstance(
        purchase_conversion_factor, (int, float)
    ):
        return bad_request("purchase_conversion_factor must be a number.")

    result = create_ingredient(
        name,
        category,
        unit,
        macros,
        purchase_unit,
        purchase_conversion_factor,
    )
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
    purchase_unit = body.get("purchase_unit")
    purchase_conversion_factor = body.get("purchase_conversion_factor")

    if name is not None and not isinstance(name, str):
        return bad_request("name must be a string.")
    if category is not None and not isinstance(category, str):
        return bad_request("category must be a string.")
    if unit is not None and not isinstance(unit, str):
        return bad_request("unit must be a string.")
    if macros is not None and not isinstance(macros, dict):
        return bad_request("macros must be a JSON object.")
    if purchase_conversion_factor is not None and not isinstance(
        purchase_conversion_factor, (int, float)
    ):
        return bad_request("purchase_conversion_factor must be a number.")

    result = update_ingredient(
        ingredient_id,
        name=name,
        category=category,
        unit=unit,
        macros=macros,
        purchase_unit=purchase_unit,
        purchase_conversion_factor=purchase_conversion_factor,
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


async def _process_openfoodfacts_ingredient_request(
    request: Request,
) -> tuple[str, str] | Response:
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
    return name.strip(), source


async def search_ingredient_handler(request: Request) -> Response:
    processed_request = await _process_openfoodfacts_ingredient_request(request)
    if isinstance(processed_request, Response):
        return processed_request
    ingredient_name, external_source = processed_request
    results = search_ingredient_from_external(ingredient_name, external_source)
    return JSONResponse(results)


async def import_ingredient_handler(request: Request) -> Response:
    processed_request = await _process_openfoodfacts_ingredient_request(request)
    if isinstance(processed_request, Response):
        return processed_request
    ingredient_name, external_source = processed_request
    result = import_ingredient_from_external(ingredient_name, external_source)
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
    unit = body.get("unit")
    min_alert_quantity = body.get("min_alert_quantity", 0.0)
    expiration_date = body.get("expiration_date")

    if not isinstance(quantity, (int, float)) or isinstance(quantity, bool):
        return bad_request("quantity is required and must be a number.")
    if not isinstance(min_alert_quantity, (int, float)) or isinstance(min_alert_quantity, bool):
        return bad_request("min_alert_quantity must be a number.")

    result = set_stock(ingredient_id, quantity, unit, min_alert_quantity, expiration_date)
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
    unit = body.get("unit", None)
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

    result = register_purchase(ingredient_id, quantity, price, purchased_at, unit, notes)
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
    category = body.get("category")
    description = body.get("description")
    portions = body.get("portions")
    steps = body.get("steps")
    ingredients = body.get("ingredients")

    if not isinstance(name, str):
        return bad_request("name is required and must be a string.")
    if not isinstance(portions, int) or isinstance(portions, bool):
        return bad_request("portions is required and must be an integer.")
    if not isinstance(ingredients, list):
        return bad_request("ingredients is required and must be a list.")

    result = create_recipe(name, portions, ingredients, category, description, steps)
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
    category = request.query_params.get("category")
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
        category=category,
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
    category = body.get("category")
    description = body.get("description")
    portions = body.get("portions")
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
        category=category,
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
    user_id = request.state.user_id
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = _parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    portions = body.get("portions")
    ingredients = body.get("ingredients")
    cooked_at = body.get("cooked_at")

    if not isinstance(portions, int) or isinstance(portions, bool):
        return bad_request("portions is required and must be an integer.")

    if ingredients is not None:
        if not isinstance(ingredients, list):
            return bad_request("ingredients must be an array.")
        for item in ingredients:
            if not isinstance(item, dict):
                return bad_request("ingredients must be an array of objects.")
            if "ingredient_id" not in item or "quantity" not in item:
                return bad_request("each ingredient entry must have ingredient_id and quantity.")
            if not isinstance(item["ingredient_id"], int) or isinstance(
                item["ingredient_id"], bool
            ):
                return bad_request("ingredient_id must be an integer.")
            if not isinstance(item["quantity"], (int, float)) or isinstance(item["quantity"], bool):
                return bad_request("quantity must be a number.")

    result = cook_recipe(recipe_id, user_id, portions, ingredients, cooked_at)
    if result.status is not FoodOperationStatus.OK:
        if result.status == FoodOperationStatus.INSUFFICIENT_STOCK:
            return insufficient_stock_response(result.missing_ingredient_ids)
        return error_response(result.status)
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

    events = list_cook_events(
        recipe_id=recipe_id_int, user_id=None, from_date=from_date, to_date=to_date
    )
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
