import json
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.requests import Request

from apps.web.api.food.routes import (
    cook_recipe_handler,
    create_ingredient_handler,
    create_purchase_handler,
    create_recipe_handler,
    delete_ingredient_handler,
    delete_recipe_handler,
    get_ingredient_handler,
    get_recipe_handler,
    list_cook_events_handler,
    list_expiring_handler,
    list_ingredients_handler,
    list_low_stock_handler,
    list_purchases_handler,
    list_recipes_handler,
    list_stock_handler,
    set_stock_handler,
    suggest_recipes_handler,
    update_ingredient_handler,
    update_recipe_handler,
)
from modules.food.types import (
    CookEvent,
    CookResult,
    FoodOperationResult,
    FoodOperationStatus,
    FoodUnit,
    Ingredient,
    IngredientMacros,
    IngredientPurchase,
    IngredientStock,
    Recipe,
    RecipeIngredient,
    RecipeMacros,
    RecipeSummary,
    SuggestResult,
)


@pytest.fixture
def mock_request():
    req = MagicMock(spec=Request)
    req.path_params = {}
    req.query_params = {}
    req.json = AsyncMock()
    return req


_INGREDIENT = Ingredient(
    1,
    "Arroz",
    "granos",
    FoodUnit.G,
    IngredientMacros.from_dict(
        {
            "serving_amount": 100,
            "serving_unit": "g",
            "kcal": 350,
            "protein_g": 7,
            "carbs_g": 77,
            "fat_g": 1,
            "fiber_g": 1,
        }
    ),
    None,
    None,
    "2026-03-15",
    "2026-03-15",
    None,
)

_STOCK = IngredientStock(1, 1, 500.0, 100.0, None, "2026-03-15")

_PURCHASE = IngredientPurchase(1, 1, 1000.0, 5990, "2026-03-15", None, "2026-03-15")

_RECIPE_INGREDIENT = RecipeIngredient(1, 1, 1, 500.0, FoodUnit.G, _INGREDIENT)

_RECIPE = Recipe(
    1, "Pollo a la plancha", None, 4, None, "2026-03-15", "2026-03-15", None, [_RECIPE_INGREDIENT]
)

_COOK_EVENT = CookEvent(1, 1, 2, "2026-03-15", "2026-03-15")

_RECIPE_SUMMARY = RecipeSummary(
    recipe=_RECIPE,
    macros=RecipeMacros(total={"kcal": 1750}, per_portion={"kcal": 437.5}),
    feasible=True,
)


def _set_json(body):
    return body


# -- Ingredients --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_ingredient_success(mock_request):
    mock_request.json.return_value = {
        "name": "Arroz",
        "category": "granos",
        "unit": "g",
        "macros": {"serving_amount": 100, "serving_unit": "g", "kcal": 350},
    }
    result = FoodOperationResult(ingredient=_INGREDIENT, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.create_ingredient", return_value=result):
        resp = await create_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.CREATED
    body = json.loads(resp.body)
    assert body["name"] == "Arroz"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_ingredient_invalid_json(mock_request):
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await create_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_ingredient_body_not_dict(mock_request):
    mock_request.json.return_value = ["not dict"]

    resp = await create_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_ingredient_missing_name(mock_request):
    mock_request.json.return_value = {
        "unit": "g",
        "macros": {"serving_amount": 100, "serving_unit": "g"},
    }

    resp = await create_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_ingredient_missing_unit(mock_request):
    mock_request.json.return_value = {
        "name": "Arroz",
        "macros": {"serving_amount": 100, "serving_unit": "g"},
    }

    resp = await create_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_ingredient_missing_macros(mock_request):
    mock_request.json.return_value = {"name": "Arroz", "unit": "g"}

    resp = await create_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_ingredient_duplicate(mock_request):
    mock_request.json.return_value = {
        "name": "Arroz",
        "unit": "g",
        "macros": {"serving_amount": 100, "serving_unit": "g"},
    }
    result = FoodOperationResult(status=FoodOperationStatus.DUPLICATE_NAME)

    with patch("apps.web.api.food.routes.create_ingredient", return_value=result):
        resp = await create_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_ingredients(mock_request):
    with patch("apps.web.api.food.routes.list_ingredients", return_value=[_INGREDIENT]):
        resp = await list_ingredients_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert len(body) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_ingredients_with_category(mock_request):
    mock_request.query_params = {"category": "granos"}

    with patch("apps.web.api.food.routes.list_ingredients", return_value=[_INGREDIENT]) as mock_fn:
        resp = await list_ingredients_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with("granos")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_ingredient_success(mock_request):
    mock_request.path_params = {"id": 1}
    result = FoodOperationResult(ingredient=_INGREDIENT, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.get_ingredient", return_value=result) as mock_fn:
        resp = await get_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with(1)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_ingredient_not_found(mock_request):
    mock_request.path_params = {"id": 999}
    result = FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    with patch("apps.web.api.food.routes.get_ingredient", return_value=result):
        resp = await get_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_ingredient_success(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"name": "Updated"}
    result = FoodOperationResult(ingredient=_INGREDIENT, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.update_ingredient", return_value=result):
        resp = await update_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_ingredient_invalid_json(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await update_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_ingredient_body_not_dict(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = ["not dict"]

    resp = await update_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_ingredient_not_found(mock_request):
    mock_request.path_params = {"id": 999}
    mock_request.json.return_value = {"name": "X"}
    result = FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    with patch("apps.web.api.food.routes.update_ingredient", return_value=result):
        resp = await update_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_ingredient_success(mock_request):
    mock_request.path_params = {"id": 1}
    result = FoodOperationResult(ingredient=_INGREDIENT, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.delete_ingredient", return_value=result):
        resp = await delete_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_ingredient_not_found(mock_request):
    mock_request.path_params = {"id": 999}
    result = FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    with patch("apps.web.api.food.routes.delete_ingredient", return_value=result):
        resp = await delete_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


# -- IngredientStock --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_stock(mock_request):
    with patch("apps.web.api.food.routes.get_stock", return_value=[_STOCK]):
        resp = await list_stock_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert len(body) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_low_stock(mock_request):
    with patch("apps.web.api.food.routes.get_low_stock", return_value=[_STOCK]):
        resp = await list_low_stock_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_expiring(mock_request):
    mock_request.query_params = {"days": "14"}

    with patch("apps.web.api.food.routes.get_expiring_soon", return_value=[_STOCK]) as mock_fn:
        resp = await list_expiring_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with(14)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_expiring_default_days(mock_request):
    with patch("apps.web.api.food.routes.get_expiring_soon", return_value=[]) as mock_fn:
        resp = await list_expiring_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with(7)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_expiring_invalid_days(mock_request):
    mock_request.query_params = {"days": "abc"}

    resp = await list_expiring_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_set_stock_success(mock_request):
    mock_request.path_params = {"ingredient_id": 1}
    mock_request.json.return_value = {"quantity": 500, "min_alert_quantity": 100}
    result = FoodOperationResult(stock=_STOCK, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.set_stock", return_value=result) as mock_fn:
        resp = await set_stock_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with(1, 500, 100, None)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_set_stock_invalid_json(mock_request):
    mock_request.path_params = {"ingredient_id": 1}
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await set_stock_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_set_stock_missing_quantity(mock_request):
    mock_request.path_params = {"ingredient_id": 1}
    mock_request.json.return_value = {}

    resp = await set_stock_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_set_stock_not_found(mock_request):
    mock_request.path_params = {"ingredient_id": 999}
    mock_request.json.return_value = {"quantity": 500}
    result = FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    with patch("apps.web.api.food.routes.set_stock", return_value=result):
        resp = await set_stock_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


# -- Purchases --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_purchase_success(mock_request):
    mock_request.json.return_value = {
        "ingredient_id": 1,
        "quantity": 1000,
        "price": 5990,
        "purchased_at": "2026-03-15",
    }
    result = FoodOperationResult(purchase=_PURCHASE, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.register_purchase", return_value=result):
        resp = await create_purchase_handler(mock_request)

    assert resp.status_code == HTTPStatus.CREATED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_purchase_invalid_json(mock_request):
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await create_purchase_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_purchase_missing_ingredient_id(mock_request):
    mock_request.json.return_value = {"quantity": 1000, "price": 5990, "purchased_at": "2026-03-15"}

    resp = await create_purchase_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_purchase_not_found(mock_request):
    mock_request.json.return_value = {
        "ingredient_id": 999,
        "quantity": 1000,
        "price": 5990,
        "purchased_at": "2026-03-15",
    }
    result = FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    with patch("apps.web.api.food.routes.register_purchase", return_value=result):
        resp = await create_purchase_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_purchases(mock_request):
    with patch("apps.web.api.food.routes.list_purchases", return_value=[_PURCHASE]):
        resp = await list_purchases_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_purchases_with_filters(mock_request):
    mock_request.query_params = {
        "ingredient_id": "1",
        "from_date": "2026-01-01",
        "to_date": "2026-12-31",
    }

    with patch("apps.web.api.food.routes.list_purchases", return_value=[_PURCHASE]) as mock_fn:
        resp = await list_purchases_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with(1, "2026-01-01", "2026-12-31")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_purchases_invalid_ingredient_id(mock_request):
    mock_request.query_params = {"ingredient_id": "abc"}

    resp = await list_purchases_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


# -- Recipes --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_recipe_success(mock_request):
    mock_request.json.return_value = {
        "name": "Pollo a la plancha",
        "portions": 4,
        "ingredients": [{"ingredient_id": 1, "quantity": 500, "unit": "g"}],
    }
    result = FoodOperationResult(recipe=_RECIPE, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.create_recipe", return_value=result):
        resp = await create_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.CREATED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_recipe_invalid_json(mock_request):
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await create_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_recipe_body_not_dict(mock_request):
    mock_request.json.return_value = ["not dict"]

    resp = await create_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_recipe_missing_name(mock_request):
    mock_request.json.return_value = {"portions": 4, "ingredients": []}

    resp = await create_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_recipe_missing_portions(mock_request):
    mock_request.json.return_value = {"name": "X", "ingredients": []}

    resp = await create_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_recipe_boolean_portions(mock_request):
    mock_request.json.return_value = {"name": "X", "portions": True, "ingredients": []}

    resp = await create_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_recipe_missing_ingredients(mock_request):
    mock_request.json.return_value = {"name": "X", "portions": 4}

    resp = await create_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_recipe_duplicate(mock_request):
    mock_request.json.return_value = {
        "name": "X",
        "portions": 4,
        "ingredients": [{"ingredient_id": 1, "quantity": 500, "unit": "g"}],
    }
    result = FoodOperationResult(status=FoodOperationStatus.DUPLICATE_NAME)

    with patch("apps.web.api.food.routes.create_recipe", return_value=result):
        resp = await create_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_recipes(mock_request):
    with patch("apps.web.api.food.routes.list_recipes", return_value=[_RECIPE]):
        resp = await list_recipes_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_recipes_with_ingredient_ids(mock_request):
    mock_request.query_params = {"ingredient_ids": "1,2,3"}

    with patch("apps.web.api.food.routes.list_recipes", return_value=[_RECIPE]) as mock_fn:
        resp = await list_recipes_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with([1, 2, 3])


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_recipes_invalid_ingredient_ids(mock_request):
    mock_request.query_params = {"ingredient_ids": "1,abc,3"}

    resp = await list_recipes_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_recipe_success(mock_request):
    mock_request.path_params = {"id": 1}
    result = FoodOperationResult(recipe=_RECIPE, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.get_recipe", return_value=result):
        resp = await get_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_recipe_not_found(mock_request):
    mock_request.path_params = {"id": 999}
    result = FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    with patch("apps.web.api.food.routes.get_recipe", return_value=result):
        resp = await get_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_recipe_success(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"name": "Updated"}
    result = FoodOperationResult(recipe=_RECIPE, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.update_recipe", return_value=result):
        resp = await update_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_recipe_invalid_json(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await update_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_recipe_body_not_dict(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = ["not dict"]

    resp = await update_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_recipe_not_found(mock_request):
    mock_request.path_params = {"id": 999}
    mock_request.json.return_value = {"name": "X"}
    result = FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    with patch("apps.web.api.food.routes.update_recipe", return_value=result):
        resp = await update_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_recipe_invalid_name_type(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"name": 123}

    resp = await update_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_recipe_invalid_ingredients_type(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"ingredients": "not a list"}

    resp = await update_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_recipe_success(mock_request):
    mock_request.path_params = {"id": 1}
    result = FoodOperationResult(recipe=_RECIPE, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.delete_recipe", return_value=result):
        resp = await delete_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_recipe_not_found(mock_request):
    mock_request.path_params = {"id": 999}
    result = FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    with patch("apps.web.api.food.routes.delete_recipe", return_value=result):
        resp = await delete_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


# -- Suggest --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_suggest_recipes(mock_request):
    suggest_result = SuggestResult(recipes=[_RECIPE_SUMMARY])
    mock_request.query_params = {"limit": "5"}

    with patch("apps.web.api.food.routes.suggest_recipes", return_value=suggest_result) as mock_fn:
        resp = await suggest_recipes_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with(5, only_with_stock=True)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_suggest_recipes_only_with_stock_false(mock_request):
    suggest_result = SuggestResult(recipes=[_RECIPE_SUMMARY])
    mock_request.query_params = {"only_with_stock": "false"}

    with patch("apps.web.api.food.routes.suggest_recipes", return_value=suggest_result) as mock_fn:
        resp = await suggest_recipes_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with(3, only_with_stock=False)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_suggest_recipes_invalid_limit(mock_request):
    mock_request.query_params = {"limit": "abc"}

    resp = await suggest_recipes_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


# -- Cook --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_success(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"portions": 2}
    cook_result = CookResult(
        cook_event=_COOK_EVENT,
        macros=RecipeMacros(total={"kcal": 875}, per_portion={"kcal": 437.5}),
        status=FoodOperationStatus.OK,
    )

    with patch("apps.web.api.food.routes.cook_recipe", return_value=cook_result) as mock_fn:
        resp = await cook_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.CREATED
    mock_fn.assert_called_once_with(1, 2, None)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_with_cooked_at(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"portions": 2, "cooked_at": "2026-03-20"}
    cook_result = CookResult(
        cook_event=_COOK_EVENT,
        macros=RecipeMacros(total={}, per_portion={}),
        status=FoodOperationStatus.OK,
    )

    with patch("apps.web.api.food.routes.cook_recipe", return_value=cook_result) as mock_fn:
        await cook_recipe_handler(mock_request)

    mock_fn.assert_called_once_with(1, 2, "2026-03-20")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_invalid_json(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await cook_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_body_not_dict(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = ["not dict"]

    resp = await cook_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_missing_portions(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {}

    resp = await cook_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_boolean_portions(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"portions": True}

    resp = await cook_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_insufficient_stock(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"portions": 2}
    cook_result = CookResult(
        cook_event=None,
        macros=None,
        status=FoodOperationStatus.INSUFFICIENT_STOCK,
        missing_ingredient_ids=[1, 2],
    )

    with patch("apps.web.api.food.routes.cook_recipe", return_value=cook_result):
        resp = await cook_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.CONFLICT
    body = json.loads(resp.body)
    assert body["missing_ingredient_ids"] == [1, 2]


# -- Cook Events --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_cook_events(mock_request):
    with patch("apps.web.api.food.routes.list_cook_events", return_value=[_COOK_EVENT]):
        resp = await list_cook_events_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_cook_events_with_filters(mock_request):
    mock_request.query_params = {
        "recipe_id": "1",
        "from_date": "2026-01-01",
        "to_date": "2026-12-31",
    }

    with patch("apps.web.api.food.routes.list_cook_events", return_value=[_COOK_EVENT]) as mock_fn:
        resp = await list_cook_events_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with(1, "2026-01-01", "2026-12-31")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_cook_events_invalid_recipe_id(mock_request):
    mock_request.query_params = {"recipe_id": "abc"}

    resp = await list_cook_events_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_recipe_boolean_portions(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"portions": True}

    resp = await update_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_ingredient_with_category_listing(mock_request):
    mock_request.query_params = {"category": "granos"}

    with patch("apps.web.api.food.routes.list_ingredients", return_value=[_INGREDIENT]) as mock_fn:
        resp = await list_ingredients_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with("granos")
