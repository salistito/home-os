from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from modules.food.macros import (
    compute_meal_macros,
    compute_recipe_macros,
)
from modules.food.service import (
    cook_recipe,
    create_ingredient,
    create_meal_entry,
    create_recipe,
    delete_ingredient,
    delete_meal_entry,
    delete_purchase,
    delete_recipe,
    get_expiring_soon,
    get_ingredient,
    get_low_stock,
    get_meal_entry,
    get_nutrition_goals,
    get_recipe,
    get_stock,
    import_ingredient_from_external,
    list_cook_events,
    list_ingredients,
    list_meal_entries,
    list_purchases,
    list_recipes,
    parse_macros,
    register_purchase,
    search_ingredient_from_external,
    set_stock,
    suggest_recipes,
    update_ingredient,
    update_meal_entry,
    update_nutrition_goals,
    update_recipe,
)
from modules.food.types import (
    CookEvent,
    FoodNutritionGoals,
    FoodOperationStatus,
    FoodUnit,
    Ingredient,
    IngredientMacros,
    IngredientPurchase,
    IngredientStock,
    MealEntry,
    MealEntryItem,
    MealItemSource,
    MealType,
    Recipe,
    RecipeIngredient,
    RecipeMacros,
)

_MACROS = {
    "serving_amount": 100,
    "serving_unit": "g",
    "kcal": 250,
    "protein_g": 26,
    "carbs_g": 0,
    "fat_g": 15,
    "fiber_g": 0,
}


@pytest.fixture
def mock_ingredient():
    return Ingredient(
        1,
        "Pechuga de pollo",
        "carnes",
        FoodUnit.G,
        IngredientMacros.from_dict(_MACROS),
        None,
        None,
        None,
        None,
        "2026-03-15",
        "2026-03-15",
        None,
    )


@pytest.fixture
def mock_stock():
    return IngredientStock(1, 1, 500.0, 100.0, None, "2026-03-15")


@pytest.fixture
def mock_purchase():
    return IngredientPurchase(1, 1, 1000.0, 5990, "2026-03-15", None, "2026-03-15")


@pytest.fixture
def mock_recipe(mock_ingredient):
    ri = RecipeIngredient(1, 1, 1, 500.0, FoodUnit.G, mock_ingredient)
    return Recipe(
        1,
        "Pollo a la plancha",
        None,
        None,
        4,
        None,
        "2026-03-15",
        "2026-03-15",
        None,
        [ri],
    )


@pytest.fixture
def mock_cook_event():
    return CookEvent(1, 1, 1, "Admin", 2, None, "2026-03-15", "2026-03-15")


# -- macros validation --


def testparse_macros_valid():
    assert parse_macros(_MACROS) is not None


def testparse_macros_not_dict():
    assert parse_macros("not a dict") is None


def testparse_macros_missing_ref_amount():
    assert parse_macros({"serving_unit": "g"}) is None


def testparse_macros_zero_ref_amount():
    m = dict(_MACROS, serving_amount=0)
    assert parse_macros(m) is None


def testparse_macros_negative_kcal():
    m = dict(_MACROS, kcal=-1)
    assert parse_macros(m) is None


# -- create_ingredient --


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_create_ingredient(mock_repo, mock_today, mock_dbdate, mock_ingredient):
    mock_today.return_value = "2026-03-15"
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_active_ingredient_by_name.return_value = None
    mock_repo.create_ingredient.return_value = mock_ingredient

    result = create_ingredient("Pechuga de pollo", "carnes", "g", _MACROS)

    assert result.status == FoodOperationStatus.OK
    assert result.ingredient.name == "Pechuga de pollo"


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_ingredient_empty_name(mock_repo):
    result = create_ingredient("  ", "carnes", "g", _MACROS)
    assert result.status == FoodOperationStatus.INVALID_NAME


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_ingredient_duplicate(mock_repo, mock_ingredient):
    mock_repo.get_active_ingredient_by_name.return_value = mock_ingredient

    result = create_ingredient("Pechuga de pollo", "carnes", "g", _MACROS)
    assert result.status == FoodOperationStatus.DUPLICATE_NAME


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_ingredient_unit_mismatch(mock_repo):
    mock_repo.get_active_ingredient_by_name.return_value = None

    macros_ml = dict(_MACROS, serving_unit="ml")
    result = create_ingredient("Leche", "lacteos", "g", macros_ml)
    assert result.status == FoodOperationStatus.INVALID_UNIT


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_ingredient_whitespace_purchase_unit_clears(mock_repo):
    mock_repo.get_active_ingredient_by_name.return_value = None

    result = create_ingredient(
        "Leche", "lacteos", "ml", dict(_MACROS, serving_unit="ml"), purchase_unit="  "
    )
    assert result.status == FoodOperationStatus.OK


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_ingredient_invalid_purchase_multiplier(mock_repo):
    mock_repo.get_active_ingredient_by_name.return_value = None

    result = create_ingredient(
        "Leche",
        "lacteos",
        "ml",
        dict(_MACROS, serving_unit="ml"),
        purchase_unit="lt",
        purchase_conversion_factor=-1,
    )
    assert result.status == FoodOperationStatus.INVALID_PURCHASE_CONVERSION_FACTOR


# -- update_active_ingredient --


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_update_ingredient(mock_repo, mock_today, mock_dbdate, mock_ingredient):
    mock_today.return_value = "2026-03-15"
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient
    mock_repo.get_active_ingredient_by_name.return_value = None
    mock_repo.update_active_ingredient.return_value = mock_ingredient

    result = update_ingredient(1, name="Pollo entero")
    assert result.status == FoodOperationStatus.OK


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_active_ingredient_not_found(mock_repo):
    mock_repo.get_active_ingredient_by_id.return_value = None

    result = update_ingredient(999, name="X")
    assert result.status == FoodOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_active_ingredient_duplicate_name(mock_repo, mock_ingredient):
    other = Ingredient(
        2,
        "Otro",
        "carnes",
        FoodUnit.G,
        IngredientMacros.from_dict(_MACROS),
        None,
        None,
        None,
        None,
        "2026-03-15",
        "2026-03-15",
        None,
    )
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient
    mock_repo.get_active_ingredient_by_name.return_value = other

    result = update_ingredient(1, name="Otro")
    assert result.status == FoodOperationStatus.DUPLICATE_NAME


# -- delete_ingredient --


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_delete_ingredient(mock_repo, mock_ingredient):
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient

    result = delete_ingredient(1)
    assert result.status == FoodOperationStatus.OK
    mock_repo.soft_delete_active_ingredient.assert_called_once_with(1)


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_delete_ingredient_not_found(mock_repo):
    mock_repo.get_active_ingredient_by_id.return_value = None

    result = delete_ingredient(999)
    assert result.status == FoodOperationStatus.NOT_FOUND


# -- get_ingredient / list_ingredients --


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_get_ingredient_found(mock_repo, mock_ingredient):
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient

    result = get_ingredient(1)
    assert result.status == FoodOperationStatus.OK


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_get_ingredient_not_found(mock_repo):
    mock_repo.get_active_ingredient_by_id.return_value = None

    result = get_ingredient(999)
    assert result.status == FoodOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_list_ingredients(mock_repo, mock_ingredient):
    mock_repo.get_active_ingredients.return_value = [mock_ingredient]

    result = list_ingredients()
    assert len(result) == 1


# -- set_stock --


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_set_stock(mock_repo, mock_today, mock_dbdate, mock_ingredient, mock_stock):
    mock_today.return_value = "2026-03-15"
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient
    mock_repo.upsert_stock.return_value = mock_stock

    result = set_stock(1, 500, min_alert_quantity=100)
    assert result.status == FoodOperationStatus.OK


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_set_stock_negative_quantity(mock_repo):
    result = set_stock(1, -1)
    assert result.status == FoodOperationStatus.INVALID_QUANTITY


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_set_stock_negative_min_alert(mock_repo):
    result = set_stock(1, 500, min_alert_quantity=-1)
    assert result.status == FoodOperationStatus.INVALID_QUANTITY


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_set_stock_non_numeric_min_alert(mock_repo):
    result = set_stock(1, 500, min_alert_quantity="abc")
    assert result.status == FoodOperationStatus.INVALID_QUANTITY


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_set_stock_ingredient_not_found(mock_repo):
    mock_repo.get_active_ingredient_by_id.return_value = None

    result = set_stock(999, 500)
    assert result.status == FoodOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_set_stock_with_purchase_unit(mock_repo, mock_today, mock_dbdate, mock_ingredient):
    mock_today.return_value = "2026-03-15"
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient
    mock_repo.upsert_stock.return_value = MagicMock()
    mock_ingredient.purchase_unit = "lt"
    mock_ingredient.purchase_conversion_factor = 1000.0

    result = set_stock(1, 3, unit="lt", min_alert_quantity=1)
    assert result.status == FoodOperationStatus.OK
    mock_repo.upsert_stock.assert_called_once_with(1, 3000.0, 1, None, "2026-03-15")


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_set_stock_with_wrong_unit(mock_repo, mock_today, mock_dbdate, mock_ingredient):
    mock_today.return_value = "2026-03-15"
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient

    result = set_stock(1, 3, unit="kg")
    assert result.status == FoodOperationStatus.INVALID_UNIT


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_get_stock(mock_repo, mock_stock):
    mock_repo.get_stock.return_value = [mock_stock]
    assert len(get_stock()) == 1


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_get_low_stock(mock_repo):
    mock_repo.get_low_stock.return_value = []
    assert get_low_stock() == []


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_get_expiring_soon(mock_repo, mock_today, mock_dbdate):
    from datetime import date

    mock_today.return_value = date(2026, 3, 15)
    mock_dbdate.return_value = "2026-04-14"
    mock_repo.get_expiring_soon.return_value = []
    result = get_expiring_soon(7)
    assert result == []
    mock_repo.get_expiring_soon.assert_called_once_with("2026-04-14")


# -- register_purchase --


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_register_purchase(mock_repo, mock_today, mock_dbdate, mock_ingredient, mock_purchase):
    mock_today.return_value = "2026-03-15"
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient
    mock_repo.create_purchase.return_value = mock_purchase
    mock_repo.adjust_stock.return_value = None

    result = register_purchase(1, 1000, 5990, "2026-03-15")
    assert result.status == FoodOperationStatus.OK
    mock_repo.adjust_stock.assert_called_once_with(1, 1000)


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_register_purchase_decimal_quantity(
    mock_repo, mock_today, mock_dbdate, mock_ingredient, mock_purchase
):
    mock_today.return_value = "2026-03-15"
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient
    mock_repo.create_purchase.return_value = mock_purchase
    mock_repo.adjust_stock.return_value = None

    result = register_purchase(1, 1.5, 5990, "2026-03-15")
    assert result.status == FoodOperationStatus.OK
    mock_repo.adjust_stock.assert_called_once_with(1, 1.5)


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_register_purchase_negative_quantity(mock_repo):
    result = register_purchase(1, 0, 5990, "2026-03-15")
    assert result.status == FoodOperationStatus.INVALID_QUANTITY


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_register_purchase_negative_price(mock_repo):
    result = register_purchase(1, 100, -1, "2026-03-15")
    assert result.status == FoodOperationStatus.INVALID_PRICE


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_register_purchase_decimal_price(mock_repo):
    result = register_purchase(1, 100, 2.5, "2026-03-15")
    assert result.status == FoodOperationStatus.INVALID_PRICE


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_register_purchase_ingredient_not_found(mock_repo):
    mock_repo.get_active_ingredient_by_id.return_value = None

    result = register_purchase(999, 100, 5990, "2026-03-15")
    assert result.status == FoodOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_register_purchase_with_purchase_unit(mock_repo, mock_today, mock_dbdate, mock_ingredient):
    mock_today.return_value = "2026-03-15"
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient
    mock_repo.create_purchase.return_value = MagicMock()
    mock_ingredient.purchase_unit = "lt"
    mock_ingredient.purchase_conversion_factor = 1000.0

    result = register_purchase(1, 3, 2000, "2026-03-15", unit="lt")
    assert result.status == FoodOperationStatus.OK


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_register_purchase_wrong_unit(mock_repo, mock_ingredient):
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient

    result = register_purchase(1, 3, 2000, "2026-03-15", unit="kg")
    assert result.status == FoodOperationStatus.INVALID_UNIT


# -- create_recipe --


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_create_recipe(mock_repo, mock_today, mock_dbdate, mock_ingredient, mock_recipe):
    mock_today.return_value = "2026-03-15"
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_active_recipe_by_name.return_value = None
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient
    mock_repo.create_recipe.return_value = mock_recipe
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe

    ingredients = [{"ingredient_id": 1, "quantity": 500, "unit": "g"}]
    result = create_recipe("Pollo a la plancha", 4, ingredients)

    assert result.status == FoodOperationStatus.OK
    mock_repo.set_recipe_ingredients.assert_called_once()


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_recipe_empty_name(mock_repo):
    result = create_recipe("  ", 4, [])
    assert result.status == FoodOperationStatus.INVALID_NAME


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_recipe_duplicate(mock_repo, mock_recipe):
    mock_repo.get_active_recipe_by_name.return_value = mock_recipe

    result = create_recipe("Pollo a la plancha", 4, [])
    assert result.status == FoodOperationStatus.DUPLICATE_NAME


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_recipe_invalid_portions(mock_repo):
    mock_repo.get_active_recipe_by_name.return_value = None

    result = create_recipe("X", 0, [])
    assert result.status == FoodOperationStatus.INVALID_PORTIONS


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_recipe_decimal_portions(mock_repo):
    mock_repo.get_active_recipe_by_name.return_value = None

    result = create_recipe("X", 2.5, [])
    assert result.status == FoodOperationStatus.INVALID_PORTIONS


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_recipe_ingredient_not_found(mock_repo):
    mock_repo.get_active_recipe_by_name.return_value = None
    mock_repo.get_active_ingredient_by_id.return_value = None

    ingredients = [{"ingredient_id": 999, "quantity": 500, "unit": "g"}]
    result = create_recipe("X", 4, ingredients)
    assert result.status == FoodOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_recipe_ingredient_unit_mismatch(mock_repo, mock_ingredient):
    mock_repo.get_active_recipe_by_name.return_value = None
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient

    ingredients = [{"ingredient_id": 1, "quantity": 500, "unit": "ml"}]
    result = create_recipe("X", 4, ingredients)
    assert result.status == FoodOperationStatus.INVALID_UNIT


# -- update_active_recipe --


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_update_recipe(mock_repo, mock_today, mock_dbdate, mock_recipe):
    mock_today.return_value = "2026-03-15"
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe
    mock_repo.get_active_recipe_by_name.return_value = None
    mock_repo.update_active_recipe.return_value = mock_recipe

    result = update_recipe(1, name="Nuevo nombre")
    assert result.status == FoodOperationStatus.OK


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_active_recipe_not_found(mock_repo):
    mock_repo.get_active_recipe_by_id.return_value = None

    result = update_recipe(999, name="X")
    assert result.status == FoodOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_recipe_decimal_portions(mock_repo, mock_recipe):
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe

    result = update_recipe(1, portions=2.5)
    assert result.status == FoodOperationStatus.INVALID_PORTIONS


# -- delete_recipe --


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_delete_recipe(mock_repo, mock_recipe):
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe

    result = delete_recipe(1)
    assert result.status == FoodOperationStatus.OK
    mock_repo.soft_delete_active_recipe.assert_called_once_with(1)


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_delete_recipe_not_found(mock_repo):
    mock_repo.get_active_recipe_by_id.return_value = None

    result = delete_recipe(999)
    assert result.status == FoodOperationStatus.NOT_FOUND


# -- cook_recipe --


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_cook_recipe(mock_repo, mock_today, mock_dbdate, mock_recipe, mock_stock, mock_cook_event):
    mock_today.return_value = "2026-03-15"
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe
    mock_repo.cook_recipe_transactional.return_value = mock_cook_event

    result = cook_recipe(1, 1, 2)

    assert result.status == FoodOperationStatus.OK
    assert result.cook_event is not None
    assert result.macros is not None
    mock_repo.cook_recipe_transactional.assert_called_once()
    call_args = mock_repo.cook_recipe_transactional.call_args
    assert call_args[0][0] == 1  # recipe_id
    assert call_args[0][1] == 1  # user_id
    assert call_args[0][2] == 2  # portions
    assert call_args[0][5] == "2026-03-15"  # cooked_at
    assert call_args[0][6] == "2026-03-15"  # created_at


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_cook_recipe_not_found(mock_repo):
    mock_repo.get_active_recipe_by_id.return_value = None

    result = cook_recipe(999, 1, 2)
    assert result.status == FoodOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_cook_recipe_invalid_portions(mock_repo, mock_recipe):
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe

    result = cook_recipe(1, 1, 0)
    assert result.status == FoodOperationStatus.INVALID_PORTIONS


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_cook_recipe_decimal_portions(mock_repo, mock_recipe):
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe

    result = cook_recipe(1, 1, 2.5)
    assert result.status == FoodOperationStatus.INVALID_PORTIONS


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_cook_recipe_insufficient_stock(
    mock_repo, mock_today, mock_dbdate, mock_recipe, mock_ingredient
):
    mock_today.return_value = "2026-03-15"
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe
    from modules.food.errors import InsufficientStockError

    mock_repo.cook_recipe_transactional.side_effect = InsufficientStockError([mock_ingredient])

    result = cook_recipe(1, 1, 2)
    assert result.status == FoodOperationStatus.INSUFFICIENT_STOCK
    assert len(result.missing_ingredient_ids) > 0


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_cook_recipe_with_ingredients(
    mock_repo, mock_today, mock_dbdate, mock_ingredient, mock_recipe, mock_cook_event
):
    mock_today.return_value = "2026-03-15"
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient
    mock_repo.cook_recipe_transactional.return_value = mock_cook_event

    ingredients_list = [
        {"ingredient_id": 1, "quantity": 200, "unit": "g"},
    ]
    result = cook_recipe(1, 1, 2, ingredients=ingredients_list)

    assert result.status == FoodOperationStatus.OK
    mock_repo.get_active_ingredient_by_id.assert_called_once_with(1)


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_cook_recipe_empty_ingredients(mock_repo):
    mock_repo.get_active_recipe_by_id.return_value = MagicMock()
    result = cook_recipe(1, 1, 2, ingredients=[])
    assert result.status == FoodOperationStatus.INVALID_COOK_INGREDIENTS


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_cook_recipe_ingredients_not_dict(mock_repo):
    mock_repo.get_active_recipe_by_id.return_value = MagicMock()
    result = cook_recipe(1, 1, 2, ingredients=["not a dict"])
    assert result.status == FoodOperationStatus.INVALID_COOK_INGREDIENTS


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_cook_recipe_ingredients_missing_id(mock_repo):
    mock_repo.get_active_recipe_by_id.return_value = MagicMock()
    result = cook_recipe(1, 1, 2, ingredients=[{"quantity": 100}])
    assert result.status == FoodOperationStatus.INVALID_COOK_INGREDIENTS


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_cook_recipe_ingredients_bad_quantity(mock_repo):
    mock_repo.get_active_recipe_by_id.return_value = MagicMock()
    result = cook_recipe(1, 1, 2, ingredients=[{"ingredient_id": 1, "quantity": -5}])
    assert result.status == FoodOperationStatus.INVALID_QUANTITY


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_cook_recipe_ingredients_not_found(mock_repo):
    mock_repo.get_active_recipe_by_id.return_value = MagicMock()
    mock_repo.get_active_ingredient_by_id.return_value = None
    result = cook_recipe(1, 1, 2, ingredients=[{"ingredient_id": 999, "quantity": 100}])
    assert result.status == FoodOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_cook_recipe_ingredients_wrong_unit(mock_repo, mock_ingredient):
    mock_repo.get_active_recipe_by_id.return_value = MagicMock()
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient
    result = cook_recipe(1, 1, 2, ingredients=[{"ingredient_id": 1, "quantity": 100, "unit": "ml"}])
    assert result.status == FoodOperationStatus.INVALID_UNIT


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_cook_recipe_no_recipe_ingredients(mock_repo):
    recipe = MagicMock()
    recipe.ingredients = []
    mock_repo.get_active_recipe_by_id.return_value = recipe
    result = cook_recipe(1, 1, 2)
    assert result.status == FoodOperationStatus.INVALID_COOK_INGREDIENTS


# -- compute_recipe_macros --


def test_compute_recipe_macros(mock_recipe):
    macros = compute_recipe_macros(mock_recipe)

    assert macros.total["kcal"] == 1250.0  # 500g * 250/100
    assert macros.total["protein_g"] == 130.0
    assert macros.per_portion["kcal"] == 312.5  # 1250 / 4


def test_compute_recipe_macros_handles_missing_ingredient():
    ri = RecipeIngredient(1, 1, 1, 500.0, FoodUnit.G, None)
    recipe = Recipe(1, "X", None, None, 2, None, "2026-03-15", "2026-03-15", None, [ri])

    macros = compute_recipe_macros(recipe)
    assert macros.total["kcal"] == 0.0


def test_compute_recipe_macros_skips_unit_mismatch():
    macros_ref = IngredientMacros(
        100,
        FoodUnit.G,
        kcal=250,
        protein_g=26,
        carbs_g=0,
        fat_g=15,
        fiber_g=0,
    )
    ing = Ingredient(
        1,
        "Pollo",
        "carnes",
        FoodUnit.UNIT,
        macros_ref,
        None,
        None,
        None,
        None,
        "2026-03-15",
        "2026-03-15",
        None,
    )
    ri = RecipeIngredient(1, 1, 1, 2.0, FoodUnit.UNIT, ing)
    recipe = Recipe(1, "X", None, None, 2, None, "2026-03-15", "2026-03-15", None, [ri])

    macros = compute_recipe_macros(recipe)
    assert macros.total["kcal"] == 0.0


# -- suggest_recipes --


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_suggest_recipes(mock_repo, mock_recipe):
    mock_repo.get_suggested_recipes.return_value = [mock_recipe]

    result = suggest_recipes(user_id=None, limit=3, only_with_stock=True)
    assert result.status == FoodOperationStatus.OK
    assert len(result.recipes) == 1
    assert result.recipes[0].feasible is True
    mock_repo.get_suggested_recipes.assert_called_once_with(None, 3, True, order_random=True)


# -- list_recipes / get_recipe --


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_list_recipes(mock_repo, mock_recipe):
    mock_repo.get_active_recipes.return_value = [mock_recipe]
    assert len(list_recipes()) == 1


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_get_recipe_found(mock_repo, mock_recipe):
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe

    result = get_recipe(1)
    assert result.status == FoodOperationStatus.OK


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_get_recipe_not_found(mock_repo):
    mock_repo.get_active_recipe_by_id.return_value = None

    result = get_recipe(999)
    assert result.status == FoodOperationStatus.NOT_FOUND


# -- list_purchases / list_cook_events --


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_list_purchases(mock_repo):
    mock_repo.get_purchases.return_value = []
    assert list_purchases() == []


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_list_cook_events(mock_repo):
    mock_repo.get_cook_events.return_value = []
    assert list_cook_events() == []


def testparse_macros_empty_reference_unit():
    m = dict(_MACROS, serving_unit="  ")
    assert parse_macros(m) is None


def testparse_macros_missing_reference_unit():
    m = dict(_MACROS)
    del m["serving_unit"]
    assert parse_macros(m) is None


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_active_ingredient_empty_name(mock_repo, mock_ingredient):
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient

    result = update_ingredient(1, name="  ")
    assert result.status == FoodOperationStatus.INVALID_NAME


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_update_active_ingredient_with_macros(mock_repo, mock_today, mock_dbdate, mock_ingredient):
    mock_today.return_value = "2026-03-15"
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient
    mock_repo.get_active_ingredient_by_name.return_value = None
    mock_repo.update_active_ingredient.return_value = mock_ingredient

    result = update_ingredient(1, macros=dict(_MACROS, kcal=300))
    assert result.status == FoodOperationStatus.OK


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_active_ingredient_with_invalid_macros(mock_repo, mock_ingredient):
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient

    result = update_ingredient(1, macros={"serving_amount": 100})
    assert result.status == FoodOperationStatus.INVALID_MACROS


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_active_ingredient_macros_unit_mismatch(mock_repo, mock_ingredient):
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient

    result = update_ingredient(1, macros=dict(_MACROS, serving_unit="ml"))
    assert result.status == FoodOperationStatus.INVALID_UNIT


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_active_ingredient_empty_unit(mock_repo, mock_ingredient):
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient

    result = update_ingredient(1, unit="  ")
    assert result.status == FoodOperationStatus.INVALID_UNIT


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_recipe_ingredient_invalid_qty_type(mock_repo, mock_ingredient):
    mock_repo.get_active_recipe_by_name.return_value = None
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient

    ingredients = [{"ingredient_id": "not_int", "quantity": 500, "unit": "g"}]
    result = create_recipe("X", 4, ingredients)
    assert result.status == FoodOperationStatus.INVALID_ID


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_recipe_ingredient_qty_zero(mock_repo, mock_ingredient):
    mock_repo.get_active_recipe_by_name.return_value = None
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient

    ingredients = [{"ingredient_id": 1, "quantity": 0, "unit": "g"}]
    result = create_recipe("X", 4, ingredients)
    assert result.status == FoodOperationStatus.INVALID_QUANTITY


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_recipe_ingredient_unit_not_str(mock_repo, mock_ingredient):
    mock_repo.get_active_recipe_by_name.return_value = None
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient

    ingredients = [{"ingredient_id": 1, "quantity": 500, "unit": 123}]
    result = create_recipe("X", 4, ingredients)
    assert result.status == FoodOperationStatus.INVALID_UNIT


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_active_recipe_empty_name(mock_repo, mock_recipe):
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe

    result = update_recipe(1, name="  ")
    assert result.status == FoodOperationStatus.INVALID_NAME


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_active_recipe_duplicate_name(mock_repo, mock_recipe):
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe
    other = Recipe(2, "Otro", None, None, 4, None, "2026-03-15", "2026-03-15", None, [])
    mock_repo.get_active_recipe_by_name.return_value = other

    result = update_recipe(1, name="Otro")
    assert result.status == FoodOperationStatus.DUPLICATE_NAME


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_active_recipe_invalid_portions(mock_repo, mock_recipe):
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe

    result = update_recipe(1, portions=0)
    assert result.status == FoodOperationStatus.INVALID_PORTIONS


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_update_active_recipe_with_ingredients(
    mock_repo, mock_today, mock_dbdate, mock_recipe, mock_ingredient
):
    mock_today.return_value = "2026-03-15"
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe
    mock_repo.get_active_recipe_by_name.return_value = None
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient
    mock_repo.update_active_recipe.return_value = mock_recipe

    ingredients = [{"ingredient_id": 1, "quantity": 300, "unit": "g"}]
    result = update_recipe(1, ingredients=ingredients)
    assert result.status == FoodOperationStatus.OK
    mock_repo.set_recipe_ingredients.assert_called_once()


def test_insufficient_stock_error():
    from modules.food.errors import InsufficientStockError
    from modules.food.types import Ingredient

    macros = IngredientMacros(serving_amount=100, serving_unit=FoodUnit.G)
    ing1 = Ingredient(
        1,
        "Arroz",
        "granos",
        FoodUnit.G,
        macros,
        None,
        None,
        None,
        None,
        "2026-01-01",
        "2026-01-01",
        None,
    )
    ing2 = Ingredient(
        2,
        "Pollo",
        "carnes",
        FoodUnit.G,
        macros,
        None,
        None,
        None,
        None,
        "2026-01-01",
        "2026-01-01",
        None,
    )
    error = InsufficientStockError([ing1, ing2])
    assert error.ingredients[0].id == 1
    assert error.ingredients[1].name == "Pollo"
    assert str(error) == "Insufficient stock for: Arroz, Pollo"


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_ingredient_invalid_macros(mock_repo):
    mock_repo.get_active_ingredient_by_name.return_value = None

    result = create_ingredient("X", None, "g", {"serving_amount": 0})
    assert result.status == FoodOperationStatus.INVALID_MACROS


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_update_active_ingredient_empty_category(
    mock_repo, mock_today, mock_dbdate, mock_ingredient
):
    mock_today.return_value = "2026-03-15"
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient
    mock_repo.get_active_ingredient_by_name.return_value = None
    mock_repo.update_active_ingredient.return_value = mock_ingredient

    result = update_ingredient(1, category="")
    assert result.status == FoodOperationStatus.OK


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_update_active_ingredient_with_unit(mock_repo, mock_today, mock_dbdate, mock_ingredient):
    mock_today.return_value = "2026-03-15"
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient
    mock_repo.get_active_ingredient_by_name.return_value = None
    mock_repo.update_active_ingredient.return_value = mock_ingredient

    result = update_ingredient(1, unit="g")
    assert result.status == FoodOperationStatus.OK


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_active_ingredient_unit_mismatch_no_macros(mock_repo, mock_ingredient):
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient

    result = update_ingredient(1, unit="ml")
    assert result.status == FoodOperationStatus.INVALID_UNIT


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_active_recipe_invalid_ingredient_qty_type(mock_repo, mock_recipe):
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe

    ingredients = [{"ingredient_id": "x", "quantity": 500, "unit": "g"}]
    result = update_recipe(1, ingredients=ingredients)
    assert result.status == FoodOperationStatus.INVALID_ID


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_active_recipe_ingredient_not_found(mock_repo, mock_recipe):
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe
    mock_repo.get_active_ingredient_by_id.return_value = None

    ingredients = [{"ingredient_id": 999, "quantity": 500, "unit": "g"}]
    result = update_recipe(1, ingredients=ingredients)
    assert result.status == FoodOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_update_active_recipe_with_description(mock_repo, mock_today, mock_dbdate, mock_recipe):
    mock_today.return_value = "2026-03-15"
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe
    mock_repo.get_active_recipe_by_name.return_value = None
    mock_repo.update_active_recipe.return_value = mock_recipe

    result = update_recipe(1, portions=6, description="New desc", steps=["s1"])
    assert result.status == FoodOperationStatus.OK


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_active_recipe_ingredient_qty_zero(mock_repo, mock_recipe):
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe

    ingredients = [{"ingredient_id": 1, "quantity": 0, "unit": "g"}]
    result = update_recipe(1, ingredients=ingredients)
    assert result.status == FoodOperationStatus.INVALID_QUANTITY


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_active_recipe_ingredient_unit_not_str(mock_repo, mock_recipe):
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe

    ingredients = [{"ingredient_id": 1, "quantity": 500, "unit": None}]
    result = update_recipe(1, ingredients=ingredients)
    assert result.status == FoodOperationStatus.INVALID_UNIT


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_active_recipe_ingredient_unit_mismatch(mock_repo, mock_recipe, mock_ingredient):
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient

    ingredients = [{"ingredient_id": 1, "quantity": 500, "unit": "ml"}]
    result = update_recipe(1, ingredients=ingredients)
    assert result.status == FoodOperationStatus.INVALID_UNIT


@pytest.mark.unit
@patch("modules.food.suggest.repository")
@patch("modules.food.service.repository")
def test_suggest_recipes_only_with_stock_false(
    mock_svc_repo, mock_suggest_repo, mock_recipe, mock_stock
):
    mock_svc_repo.get_suggested_recipes.return_value = [mock_recipe]
    mock_suggest_repo.get_stock_by_ingredient_id.return_value = mock_stock

    result = suggest_recipes(user_id=None, limit=3, only_with_stock=False)
    assert result.status == FoodOperationStatus.OK
    assert len(result.recipes) == 1
    assert result.recipes[0].feasible is True
    mock_svc_repo.get_suggested_recipes.assert_called_once_with(None, 3, False, order_random=True)


@pytest.mark.unit
@patch("modules.food.suggest.repository")
@patch("modules.food.service.repository")
def test_suggest_recipes_only_with_stock_false_infeasible(
    mock_svc_repo, mock_suggest_repo, mock_recipe
):
    mock_svc_repo.get_suggested_recipes.return_value = [mock_recipe]
    mock_suggest_repo.get_stock_by_ingredient_id.return_value = None

    result = suggest_recipes(user_id=None, limit=3, only_with_stock=False)
    assert result.recipes[0].feasible is False


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_list_recipes_with_ingredient_ids(mock_repo, mock_recipe):
    mock_repo.get_active_recipes.return_value = [mock_recipe]

    result = list_recipes(ingredient_ids=[1, 2])
    assert len(result) == 1
    mock_repo.get_active_recipes.assert_called_once_with([1, 2])


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_list_recipes_no_filter(mock_repo, mock_recipe):
    mock_repo.get_active_recipes.return_value = [mock_recipe]

    result = list_recipes()
    assert len(result) == 1
    mock_repo.get_active_recipes.assert_called_once_with(None)


@pytest.mark.integration
def test_cook_recipe_transactional(db, db_user, frozen_today):
    import modules.food.repository as repo
    from modules.food.types import CookEventIngredient, RecipeMacros

    ing = repo.create_ingredient(
        "Pechuga de pollo",
        "carnes",
        FoodUnit.G,
        IngredientMacros(
            serving_amount=100,
            serving_unit=FoodUnit.G,
            kcal=250,
            protein_g=26,
            carbs_g=0,
            fat_g=15,
            fiber_g=0,
        ),
        "2026-03-15",
        "2026-03-15",
    )
    recipe = repo.create_recipe("Pollo", None, None, 2, None, "2026-03-15", "2026-03-15")
    repo.set_recipe_ingredients(recipe.id, [(ing.id, 300, FoodUnit.G)])
    repo.upsert_stock(ing.id, 500, 0, None, "2026-03-15")

    cei = CookEventIngredient(
        id=0,
        cook_event_id=None,
        ingredient_id=ing.id,
        ingredient_name=ing.name,
        quantity=300.0,
        unit=FoodUnit.G,
        macros=ing.macros,
    )
    macros = RecipeMacros(total={"kcal": 750.0}, per_portion={"kcal": 375.0})

    cook_event = repo.cook_recipe_transactional(
        recipe.id, db_user.id, 2, macros, [cei], "2026-03-15", "2026-03-15"
    )
    assert cook_event is not None
    assert cook_event.recipe_id == recipe.id
    assert cook_event.portions == 2
    assert cook_event.macros is not None
    assert len(cook_event.ingredients) == 1
    assert cook_event.ingredients[0].ingredient_name == "Pechuga de pollo"

    stock = repo.get_stock_by_ingredient_id(ing.id)
    assert stock.quantity == 200.0


@pytest.mark.integration
def test_cook_recipe_transactional_insufficient(db, db_user, frozen_today):
    import modules.food.repository as repo
    from modules.food.errors import InsufficientStockError
    from modules.food.types import CookEventIngredient, RecipeMacros

    ing = repo.create_ingredient(
        "Pechuga de pollo",
        "carnes",
        FoodUnit.G,
        IngredientMacros(
            serving_amount=100,
            serving_unit=FoodUnit.G,
            kcal=250,
            protein_g=26,
            carbs_g=0,
            fat_g=15,
            fiber_g=0,
        ),
        "2026-03-15",
        "2026-03-15",
    )
    recipe = repo.create_recipe("Pollo", None, None, 2, None, "2026-03-15", "2026-03-15")
    repo.set_recipe_ingredients(recipe.id, [(ing.id, 300, FoodUnit.G)])
    repo.upsert_stock(ing.id, 100, 0, None, "2026-03-15")

    cei = CookEventIngredient(
        id=0,
        cook_event_id=None,
        ingredient_id=ing.id,
        ingredient_name=ing.name,
        quantity=300.0,
        unit=FoodUnit.G,
        macros=ing.macros,
    )
    macros = RecipeMacros(total={"kcal": 750.0}, per_portion={"kcal": 375.0})

    with pytest.raises(InsufficientStockError) as exc_info:
        repo.cook_recipe_transactional(
            recipe.id, db_user.id, 2, macros, [cei], "2026-03-15", "2026-03-15"
        )
    assert exc_info.value.ingredients[0].id == 1

    stock = repo.get_stock_by_ingredient_id(ing.id)
    assert stock.quantity == 100.0


@pytest.mark.integration
def test_cook_recipe_transactional_rollback_multiple(db, db_user, frozen_today):
    import modules.food.repository as repo
    from modules.food.errors import InsufficientStockError
    from modules.food.types import CookEventIngredient, RecipeMacros

    ing1 = repo.create_ingredient(
        "Arroz",
        "granos",
        FoodUnit.G,
        IngredientMacros(
            serving_amount=100,
            serving_unit=FoodUnit.G,
            kcal=350,
            protein_g=7,
            carbs_g=77,
            fat_g=1,
            fiber_g=1,
        ),
        "2026-03-15",
        "2026-03-15",
    )
    ing2 = repo.create_ingredient(
        "Pechuga de pollo",
        "carnes",
        FoodUnit.G,
        IngredientMacros(
            serving_amount=100,
            serving_unit=FoodUnit.G,
            kcal=250,
            protein_g=26,
            carbs_g=0,
            fat_g=15,
            fiber_g=0,
        ),
        "2026-03-15",
        "2026-03-15",
    )
    recipe = repo.create_recipe("Arroz con pollo", None, None, 2, None, "2026-03-15", "2026-03-15")
    repo.set_recipe_ingredients(recipe.id, [(ing1.id, 200, FoodUnit.G), (ing2.id, 300, FoodUnit.G)])
    repo.upsert_stock(ing1.id, 500, 0, None, "2026-03-15")
    repo.upsert_stock(ing2.id, 100, 0, None, "2026-03-15")

    ceis = [
        CookEventIngredient(
            id=0,
            cook_event_id=None,
            ingredient_id=ing1.id,
            ingredient_name=ing1.name,
            quantity=200.0,
            unit=FoodUnit.G,
            macros=ing1.macros,
        ),
        CookEventIngredient(
            id=0,
            cook_event_id=None,
            ingredient_id=ing2.id,
            ingredient_name=ing2.name,
            quantity=300.0,
            unit=FoodUnit.G,
            macros=ing2.macros,
        ),
    ]
    macros = RecipeMacros(total={"kcal": 750.0}, per_portion={"kcal": 375.0})

    with pytest.raises(InsufficientStockError):
        repo.cook_recipe_transactional(
            recipe.id, db_user.id, 2, macros, ceis, "2026-03-15", "2026-03-15"
        )

    stock1 = repo.get_stock_by_ingredient_id(ing1.id)
    stock2 = repo.get_stock_by_ingredient_id(ing2.id)
    assert stock1.quantity == 500.0
    assert stock2.quantity == 100.0


def test_ingredient_already_exists_error():
    from modules.food.errors import IngredientAlreadyExistsError
    from modules.food.types import Ingredient

    macros = IngredientMacros(serving_amount=100, serving_unit=FoodUnit.G)
    ing = Ingredient(
        1,
        "Arroz",
        "granos",
        FoodUnit.G,
        macros,
        None,
        None,
        None,
        None,
        "2026-01-01",
        "2026-01-01",
        None,
    )
    error = IngredientAlreadyExistsError(ing)
    assert error.ingredient == ing
    assert str(error) == "Ingredient 'Arroz' already exists."


def test_recipe_already_exists_error():
    from modules.food.errors import RecipeAlreadyExistsError
    from modules.food.types import Recipe

    recipe = Recipe(1, "Pollo", None, 4, None, "2026-01-01", "2026-01-01", None, [])
    error = RecipeAlreadyExistsError(recipe)
    assert error.recipe == recipe
    assert str(error) == "Recipe 'Pollo' already exists."


# -- delete_purchase --


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_delete_purchase_success(mock_repo, mock_purchase):
    stock = IngredientStock(1, 1, 1500.0, 100.0, None, "2026-03-15")
    mock_repo.get_purchase_by_id.return_value = mock_purchase
    mock_repo.get_stock_by_ingredient_id.return_value = stock
    mock_repo.delete_purchase.return_value = mock_purchase

    result = delete_purchase(1)

    assert result.status == FoodOperationStatus.OK
    assert result.purchase == mock_purchase
    mock_repo.adjust_stock.assert_called_once_with(1, -1000.0)


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_delete_purchase_not_found(mock_repo):
    mock_repo.get_purchase_by_id.return_value = None

    result = delete_purchase(999)

    assert result.status == FoodOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_delete_purchase_insufficient_stock(mock_repo, mock_purchase):
    stock = IngredientStock(1, 1, 50.0, 100.0, None, "2026-03-15")
    mock_repo.get_purchase_by_id.return_value = mock_purchase
    mock_repo.get_stock_by_ingredient_id.return_value = stock

    result = delete_purchase(1)

    assert result.status == FoodOperationStatus.CANNOT_REVERT_PURCHASE
    mock_repo.adjust_stock.assert_not_called()


# -- import_ingredient_from_external --


@pytest.mark.unit
@patch("modules.food.service.repository")
@patch("modules.food.external.search_open_food_facts")
def test_import_ingredient_from_external_success(mock_search, mock_repo):
    mock_search.return_value = [
        {
            "code": "123456",
            "product_name": "Arroz integral",
            "serving_quantity": "100",
            "serving_size": "100 g",
            "nutriments": {
                "energy-kcal_serving": 350,
                "proteins_serving": 7.0,
                "carbohydrates_serving": 78.0,
                "fat_serving": 2.5,
                "fiber_serving": 3.5,
            },
        }
    ]
    mock_repo.get_active_ingredient_by_name.return_value = None
    mock_repo.create_ingredient.return_value = MagicMock()

    result = import_ingredient_from_external("arroz")

    assert result.status == FoodOperationStatus.OK
    mock_repo.create_ingredient.assert_called_once()


@pytest.mark.unit
@patch("modules.food.service.repository")
@patch("modules.food.external.search_open_food_facts")
def test_import_ingredient_from_external_not_found(mock_search, mock_repo):
    mock_search.return_value = []
    mock_repo.get_active_ingredient_by_name.return_value = None

    result = import_ingredient_from_external("xyz")

    assert result.status == FoodOperationStatus.EXTERNAL_NOT_FOUND


@pytest.mark.unit
@patch("modules.food.service.repository")
@patch("modules.food.external.search_open_food_facts")
def test_import_ingredient_from_external_empty_name(mock_search, mock_repo):
    result = import_ingredient_from_external("")

    assert result.status == FoodOperationStatus.INVALID_NAME
    mock_search.assert_not_called()


@pytest.mark.unit
@patch("modules.food.service.repository")
@patch("modules.food.external.search_open_food_facts")
def test_import_ingredient_from_external_duplicate(mock_search, mock_repo):
    mock_search.return_value = [{"code": "123", "product_name": "Arroz"}]
    mock_repo.get_active_ingredient_by_name.return_value = MagicMock()

    result = import_ingredient_from_external("arroz")

    assert result.status == FoodOperationStatus.DUPLICATE_NAME


@pytest.mark.unit
@patch("modules.food.service.repository")
@patch("modules.food.external.search_open_food_facts")
def test_import_ingredient_from_external_network_error(mock_search, mock_repo):
    mock_search.side_effect = Exception("network error")
    mock_repo.get_active_ingredient_by_name.return_value = None

    result = import_ingredient_from_external("arroz")

    assert result.status == FoodOperationStatus.EXTERNAL_NOT_FOUND


@pytest.mark.unit
@patch("modules.food.external.search_open_food_facts")
def test_search_external_ingredient_success(mock_search):
    mock_search.return_value = [
        {
            "code": "123456",
            "product_name": "Arroz integral",
            "serving_quantity": "100",
            "serving_size": "100 g",
            "nutriments": {
                "energy-kcal_serving": 350,
                "proteins_serving": 7.0,
                "carbohydrates_serving": 78.0,
                "fat_serving": 2.5,
                "fiber_serving": 3.5,
            },
        }
    ]

    results = search_ingredient_from_external("arroz")

    assert len(results) == 1
    assert results[0]["name"] == "Arroz integral"
    assert results[0]["external_id"] == "123456"
    assert results[0]["source"] == "openfoodfacts"
    assert results[0]["macros"]["kcal"] == 350
    mock_search.assert_called_once_with("arroz")


@pytest.mark.unit
@patch("modules.food.external.search_open_food_facts")
def test_search_external_ingredient_empty_name(mock_search):
    results = search_ingredient_from_external("")

    assert results == []
    mock_search.assert_not_called()


@pytest.mark.unit
@patch("modules.food.external.search_open_food_facts")
def test_search_external_ingredient_not_found(mock_search):
    mock_search.return_value = []

    results = search_ingredient_from_external("xyz")

    assert results == []


@pytest.mark.unit
@patch("modules.food.external.search_open_food_facts")
def test_search_external_ingredient_network_error(mock_search):
    mock_search.side_effect = Exception("network error")

    results = search_ingredient_from_external("arroz")

    assert results == []


# -- Nutrition goals --


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_get_nutrition_goals(mock_repo):
    goals = FoodNutritionGoals(1, 1, 2000, 100, 250, 70, "2026-03-15")
    mock_repo.get_nutrition_goals.return_value = goals

    result = get_nutrition_goals(1)

    assert result.status == FoodOperationStatus.OK
    assert result.goals.kcal_target == 2000
    assert result.goals.protein_g_target == 100
    mock_repo.get_nutrition_goals.assert_called_once_with(1)


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_get_nutrition_goals_not_found(mock_repo):
    mock_repo.get_nutrition_goals.return_value = None

    result = get_nutrition_goals(1)

    assert result.status == FoodOperationStatus.NOT_FOUND
    assert result.goals is None


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_update_nutrition_goals(mock_repo, mock_today, mock_dbdate):
    mock_today.return_value = "2026-03-15"
    mock_dbdate.return_value = "2026-03-15"
    goals = FoodNutritionGoals(1, 1, 2000, 100, 250, 70, "2026-03-15")
    mock_repo.upsert_nutrition_goals.return_value = goals

    result = update_nutrition_goals(user_id=1, kcal_target=2000, protein_g_target=100)

    assert result.status == FoodOperationStatus.OK
    assert result.goals.kcal_target == 2000
    mock_repo.upsert_nutrition_goals.assert_called_once()


@pytest.mark.unit
def test_update_nutrition_goals_invalid_kcal():
    result = update_nutrition_goals(user_id=1, kcal_target=2000.5)
    assert result.status == FoodOperationStatus.INVALID_MACROS


@pytest.mark.unit
def test_update_nutrition_goals_invalid_protein():
    result = update_nutrition_goals(user_id=1, protein_g_target="bad")
    assert result.status == FoodOperationStatus.INVALID_MACROS


# -- Meal entries --


def _compute_meal_item(kcal=100.0, protein=10.0):
    return SimpleNamespace(
        macros={"kcal": kcal, "protein_g": protein, "carbs_g": 5.0, "fat_g": 2.0, "fiber_g": 1.0}
    )


def test_compute_meal_macros_sums_items():
    items = [_compute_meal_item(kcal=100.0), _compute_meal_item(kcal=150.5, protein=20.0)]
    total = compute_meal_macros(items)
    assert total["kcal"] == 250.5
    assert total["protein_g"] == 30.0


def test_compute_meal_macros_ignores_missing_and_none():
    items = [
        SimpleNamespace(macros={"kcal": 100.0, "protein_g": None}),
        SimpleNamespace(macros=None),
        SimpleNamespace(macros={"kcal": "bad"}),
    ]
    total = compute_meal_macros(items)
    assert total["kcal"] == 100.0
    assert total["protein_g"] == 0.0


def _meal_entry_factory(
    entry_id=1,
    items=None,
    macros=None,
    meal_type=MealType.LUNCH,
    eaten_at="2026-03-15T12:30",
):
    return MealEntry(
        entry_id,
        1,
        "Admin",
        meal_type,
        macros if macros is not None else {"kcal": 1000.0},
        None,
        eaten_at,
        "2026-03-15",
        items if items is not None else [],
    )


def _manual_item(name="x", kcal=10, macros=None):
    return {
        "source": "manual",
        "name": name,
        "macros": macros if macros is not None else {"kcal": kcal},
    }


def _cook_event_meal_item(portions=2.0, event_id=7):
    return MealEntryItem(
        id=1,
        meal_entry_id=1,
        source=MealItemSource.COOK_EVENT,
        name="Pollo a la plancha",
        macros={
            "kcal": 1000.0,
            "protein_g": 40.0,
            "carbs_g": 100.0,
            "fat_g": 20.0,
            "fiber_g": 10.0,
        },
        cook_event_id=event_id,
        portions=portions,
    )


def _cook_event_with_macros(event_id=7):
    return CookEvent(
        event_id,
        1,
        1,
        "Admin",
        4,
        RecipeMacros(
            total={"kcal": 2000, "protein_g": 80, "carbs_g": 200, "fat_g": 40, "fiber_g": 20},
            per_portion={"kcal": 500, "protein_g": 20, "carbs_g": 50, "fat_g": 10, "fiber_g": 5},
        ),
        "2026-03-15",
        "2026-03-15",
    )


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_create_meal_entry_cook_event(mock_repo, mock_today, mock_dbdate, mock_recipe):
    mock_today.return_value = date(2026, 3, 15)
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_cook_event_by_id.return_value = _cook_event_with_macros()
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe
    mock_repo.get_cook_event_availability.return_value = ("2026-03-15", 10.0)
    entry = _meal_entry_factory()
    mock_repo.create_meal_entry.return_value = entry

    result = create_meal_entry(
        1,
        "lunch",
        "2026-03-15T12:30",
        [{"source": "cook_event", "cook_event_id": 7, "portions": 2}],
    )

    assert result.status == FoodOperationStatus.OK
    assert result.meal_entry is entry
    call_args = mock_repo.create_meal_entry.call_args
    assert call_args.kwargs["meal_type"] == MealType.LUNCH
    assert call_args.kwargs["macros"] == {
        "kcal": 1000.0,
        "protein_g": 40.0,
        "carbs_g": 100.0,
        "fat_g": 20.0,
        "fiber_g": 10.0,
    }
    item = call_args.kwargs["items"][0]
    assert item.source == MealItemSource.COOK_EVENT
    assert item.cook_event_id == 7
    assert item.portions == 2.0
    assert item.name == "Pollo a la plancha"
    assert item.macros["kcal"] == 1000.0


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_create_meal_entry_cook_event_fractional_portions(
    mock_repo, mock_today, mock_dbdate, mock_recipe
):
    mock_today.return_value = date(2026, 3, 15)
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_cook_event_by_id.return_value = _cook_event_with_macros()
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe
    mock_repo.get_cook_event_availability.return_value = ("2026-03-15", 10.0)
    mock_repo.create_meal_entry.return_value = _meal_entry_factory()

    result = create_meal_entry(
        1,
        "lunch",
        "2026-03-15T12:30",
        [{"source": "cook_event", "cook_event_id": 7, "portions": 0.5}],
    )

    assert result.status == FoodOperationStatus.OK
    item = mock_repo.create_meal_entry.call_args.kwargs["items"][0]
    assert item.portions == 0.5
    assert item.macros["kcal"] == 250.0


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_meal_entry_manual(mock_repo):
    mock_repo.create_meal_entry.return_value = _meal_entry_factory()

    result = create_meal_entry(
        1,
        "snack",
        "2026-03-15T13:00",
        [
            {
                "source": "manual",
                "name": "  Hamburguesa  ",
                "macros": {"kcal": 500, "protein_g": 25},
            }
        ],
    )

    assert result.status == FoodOperationStatus.OK
    call_args = mock_repo.create_meal_entry.call_args
    assert call_args.kwargs["meal_type"] == MealType.SNACK
    assert call_args.kwargs["macros"] == {
        "kcal": 500.0,
        "protein_g": 25.0,
        "carbs_g": 0.0,
        "fat_g": 0.0,
        "fiber_g": 0.0,
    }
    item = call_args.kwargs["items"][0]
    assert item.source == MealItemSource.MANUAL
    assert item.name == "Hamburguesa"
    assert item.cook_event_id is None


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_meal_entry_invalid_meal_type(mock_repo):
    result = create_meal_entry(1, "brunch", "2026-03-15T12:30", [_manual_item()])
    assert result.status == FoodOperationStatus.INVALID_MEAL_TYPE


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_meal_entry_invalid_eaten_at(mock_repo):
    result = create_meal_entry(1, "lunch", "  ", [_manual_item()])
    assert result.status == FoodOperationStatus.INVALID_EATEN_AT


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_meal_entry_empty_items(mock_repo):
    result = create_meal_entry(1, "lunch", "2026-03-15T12:30", [])
    assert result.status == FoodOperationStatus.INVALID_MEAL_ITEM


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_meal_entry_invalid_source(mock_repo):
    result = create_meal_entry(
        1, "lunch", "2026-03-15T12:30", [{"source": "recipe", "name": "x"}]
    )
    assert result.status == FoodOperationStatus.INVALID_MEAL_ITEM_SOURCE


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_meal_entry_cook_event_not_found(mock_repo):
    mock_repo.get_cook_event_by_id.return_value = None

    result = create_meal_entry(
        1,
        "lunch",
        "2026-03-15T12:30",
        [{"source": "cook_event", "cook_event_id": 999, "portions": 1}],
    )
    assert result.status == FoodOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_meal_entry_cook_event_invalid_portions(mock_repo):
    mock_repo.get_cook_event_by_id.return_value = _cook_event_with_macros()

    result = create_meal_entry(
        1,
        "lunch",
        "2026-03-15T12:30",
        [{"source": "cook_event", "cook_event_id": 7, "portions": 0}],
    )
    assert result.status == FoodOperationStatus.INVALID_PORTIONS


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_create_meal_entry_insufficient_portions(
    mock_repo, mock_today, mock_dbdate, mock_recipe
):
    mock_today.return_value = date(2026, 3, 15)
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_cook_event_by_id.return_value = _cook_event_with_macros()
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe
    mock_repo.get_cook_event_availability.return_value = ("2026-03-15", 1.0)

    result = create_meal_entry(
        1,
        "lunch",
        "2026-03-15T12:30",
        [{"source": "cook_event", "cook_event_id": 7, "portions": 2}],
    )

    assert result.status == FoodOperationStatus.INSUFFICIENT_PORTIONS
    mock_repo.create_meal_entry.assert_not_called()


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_create_meal_entry_expired_cook_event(mock_repo, mock_today, mock_dbdate, mock_recipe):
    mock_today.return_value = date(2026, 3, 15)
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_cook_event_by_id.return_value = _cook_event_with_macros()
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe
    mock_repo.get_cook_event_availability.return_value = ("2026-03-01", 10.0)

    result = create_meal_entry(
        1,
        "lunch",
        "2026-03-15T12:30",
        [{"source": "cook_event", "cook_event_id": 7, "portions": 2}],
    )

    assert result.status == FoodOperationStatus.EXPIRED_COOK_EVENT
    mock_repo.create_meal_entry.assert_not_called()


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_create_meal_entry_cook_event_availability_not_found(
    mock_repo, mock_today, mock_dbdate, mock_recipe
):
    mock_today.return_value = date(2026, 3, 15)
    mock_dbdate.return_value = "2026-03-15"
    mock_repo.get_cook_event_by_id.return_value = _cook_event_with_macros()
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe
    mock_repo.get_cook_event_availability.return_value = None

    result = create_meal_entry(
        1,
        "lunch",
        "2026-03-15T12:30",
        [{"source": "cook_event", "cook_event_id": 7, "portions": 2}],
    )

    assert result.status == FoodOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_meal_entry_manual_missing_kcal(mock_repo):
    result = create_meal_entry(
        1, "lunch", "2026-03-15T12:30", [_manual_item(macros={"protein_g": 10})]
    )
    assert result.status == FoodOperationStatus.INVALID_MACROS


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_meal_entry_manual_negative_macro(mock_repo):
    result = create_meal_entry(1, "lunch", "2026-03-15T12:30", [_manual_item(kcal=-5)])
    assert result.status == FoodOperationStatus.INVALID_MACROS


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_meal_entry_manual_invalid_name(mock_repo):
    result = create_meal_entry(
        1, "lunch", "2026-03-15T12:30", [_manual_item(name="  ")]
    )
    assert result.status == FoodOperationStatus.INVALID_NAME


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_meal_entry_ingredient(mock_repo, mock_ingredient):
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient
    mock_repo.create_meal_entry.return_value = _meal_entry_factory()

    result = create_meal_entry(
        1,
        "lunch",
        "2026-03-15T12:30",
        [{"source": "ingredient", "ingredient_id": 1, "quantity": 200, "unit": "g"}],
    )

    assert result.status == FoodOperationStatus.OK
    call_args = mock_repo.create_meal_entry.call_args
    item = call_args.kwargs["items"][0]
    assert item.source == MealItemSource.INGREDIENT
    assert item.name == "Pechuga de pollo"
    assert item.ingredient_id == 1
    assert item.quantity == 200.0
    assert item.unit == FoodUnit.G
    assert item.cook_event_id is None
    assert item.portions is None
    assert item.macros["kcal"] == 500.0
    assert item.macros["protein_g"] == 52.0
    assert item.macros["fat_g"] == 30.0
    assert call_args.kwargs["macros"] == {
        "kcal": 500.0,
        "protein_g": 52.0,
        "carbs_g": 0.0,
        "fat_g": 30.0,
        "fiber_g": 0.0,
    }


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_meal_entry_ingredient_defaults_to_ingredient_unit(mock_repo, mock_ingredient):
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient
    mock_repo.create_meal_entry.return_value = _meal_entry_factory()

    result = create_meal_entry(
        1,
        "lunch",
        "2026-03-15T12:30",
        [{"source": "ingredient", "ingredient_id": 1, "quantity": 50}],
    )

    assert result.status == FoodOperationStatus.OK
    item = mock_repo.create_meal_entry.call_args.kwargs["items"][0]
    assert item.unit == FoodUnit.G
    assert item.macros["kcal"] == 125.0


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_meal_entry_ingredient_not_found(mock_repo):
    mock_repo.get_active_ingredient_by_id.return_value = None

    result = create_meal_entry(
        1,
        "lunch",
        "2026-03-15T12:30",
        [{"source": "ingredient", "ingredient_id": 999, "quantity": 100, "unit": "g"}],
    )
    assert result.status == FoodOperationStatus.NOT_FOUND
    mock_repo.create_meal_entry.assert_not_called()


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_meal_entry_ingredient_invalid_quantity(mock_repo, mock_ingredient):
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient

    result = create_meal_entry(
        1,
        "lunch",
        "2026-03-15T12:30",
        [{"source": "ingredient", "ingredient_id": 1, "quantity": 0, "unit": "g"}],
    )
    assert result.status == FoodOperationStatus.INVALID_QUANTITY


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_meal_entry_ingredient_invalid_unit(mock_repo, mock_ingredient):
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient

    result = create_meal_entry(
        1,
        "lunch",
        "2026-03-15T12:30",
        [{"source": "ingredient", "ingredient_id": 1, "quantity": 100, "unit": "kg"}],
    )
    assert result.status == FoodOperationStatus.INVALID_UNIT


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_create_meal_entry_ingredient_insufficient_stock(mock_repo, mock_ingredient):
    from modules.food.errors import InsufficientStockError

    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient
    mock_repo.create_meal_entry.side_effect = InsufficientStockError([mock_ingredient])

    result = create_meal_entry(
        1,
        "lunch",
        "2026-03-15T12:30",
        [{"source": "ingredient", "ingredient_id": 1, "quantity": 100, "unit": "g"}],
    )
    assert result.status == FoodOperationStatus.INSUFFICIENT_STOCK
    assert result.missing_ingredient_ids == [1]


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_meal_entry_ingredient_insufficient_stock(mock_repo, mock_ingredient):
    from modules.food.errors import InsufficientStockError

    entry = _meal_entry_factory(items=[_cook_event_meal_item(portions=1.0)])
    mock_repo.get_meal_entry_by_id_and_user_id.return_value = entry
    mock_repo.get_active_ingredient_by_id.return_value = mock_ingredient
    mock_repo.update_meal_entry.side_effect = InsufficientStockError([mock_ingredient])

    result = update_meal_entry(
        1,
        1,
        items=[{"source": "ingredient", "ingredient_id": 1, "quantity": 100, "unit": "g"}],
    )
    assert result.status == FoodOperationStatus.INSUFFICIENT_STOCK
    assert result.missing_ingredient_ids == [1]


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_get_meal_entry(mock_repo):
    entry = _meal_entry_factory()
    mock_repo.get_meal_entry_by_id_and_user_id.return_value = entry

    result = get_meal_entry(1, 1)

    assert result.status == FoodOperationStatus.OK
    assert result.meal_entry is entry
    mock_repo.get_meal_entry_by_id_and_user_id.assert_called_once_with(1, 1)


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_get_meal_entry_not_found(mock_repo):
    mock_repo.get_meal_entry_by_id_and_user_id.return_value = None

    result = get_meal_entry(1, 1)

    assert result.status == FoodOperationStatus.NOT_FOUND
    assert result.meal_entry is None


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_list_meal_entries(mock_repo):
    mock_repo.get_meal_entries.return_value = [_meal_entry_factory()]

    result = list_meal_entries(1, from_date="2026-03-15", to_date="2026-03-15")

    assert len(result) == 1
    mock_repo.get_meal_entries.assert_called_once_with(1, "2026-03-15", "2026-03-15")


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_meal_entry(mock_repo):
    entry = _meal_entry_factory(eaten_at="2026-03-16T08:00")
    mock_repo.get_meal_entry_by_id_and_user_id.return_value = entry

    result = update_meal_entry(
        1,
        1,
        eaten_at="2026-03-16T08:00",
        meal_type="breakfast",
        notes="sin pan",
    )

    assert result.status == FoodOperationStatus.OK
    assert result.meal_entry.eaten_at == "2026-03-16T08:00"
    mock_repo.update_meal_entry.assert_called_once_with(
        1, eaten_at="2026-03-16T08:00", meal_type=MealType.BREAKFAST, notes="sin pan"
    )


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_meal_entry_with_items(mock_repo):
    mock_repo.get_meal_entry_by_id_and_user_id.return_value = _meal_entry_factory()

    result = update_meal_entry(
        1,
        1,
        items=[{"source": "manual", "name": "Cafe", "macros": {"kcal": 60}}],
    )

    assert result.status == FoodOperationStatus.OK
    call_args = mock_repo.update_meal_entry.call_args
    assert call_args.kwargs["macros"] == {
        "kcal": 60.0,
        "protein_g": 0.0,
        "carbs_g": 0.0,
        "fat_g": 0.0,
        "fiber_g": 0.0,
    }


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_update_meal_entry_insufficient_portions_excludes_own_items(
    mock_repo, mock_today, mock_dbdate, mock_recipe
):
    mock_today.return_value = date(2026, 3, 15)
    mock_dbdate.return_value = "2026-03-15"
    entry = _meal_entry_factory(items=[_cook_event_meal_item(portions=2.0)])
    mock_repo.get_meal_entry_by_id_and_user_id.return_value = entry
    mock_repo.get_cook_event_by_id.return_value = _cook_event_with_macros()
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe
    mock_repo.get_cook_event_availability.return_value = ("2026-03-15", 1.0)

    result = update_meal_entry(
        1,
        1,
        items=[{"source": "cook_event", "cook_event_id": 7, "portions": 2}],
    )

    assert result.status == FoodOperationStatus.INSUFFICIENT_PORTIONS
    mock_repo.get_cook_event_availability.assert_called_once_with(7, 1)
    mock_repo.update_meal_entry.assert_not_called()


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_update_meal_entry_grandfathers_own_old_event(
    mock_repo, mock_today, mock_dbdate, mock_recipe
):
    mock_today.return_value = date(2026, 3, 15)
    mock_dbdate.return_value = "2026-03-15"
    entry = _meal_entry_factory(items=[_cook_event_meal_item(portions=2.0)])
    mock_repo.get_meal_entry_by_id_and_user_id.return_value = entry
    mock_repo.get_cook_event_by_id.return_value = _cook_event_with_macros()
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe
    mock_repo.get_cook_event_availability.return_value = ("2026-02-20", 10.0)

    result = update_meal_entry(
        1,
        1,
        items=[{"source": "cook_event", "cook_event_id": 7, "portions": 2}],
    )

    assert result.status == FoodOperationStatus.OK


@pytest.mark.unit
@patch("modules.food.service.to_db_date")
@patch("modules.food.service.get_today")
@patch("modules.food.service.repository")
def test_update_meal_entry_rejects_new_old_event(mock_repo, mock_today, mock_dbdate, mock_recipe):
    mock_today.return_value = date(2026, 3, 15)
    mock_dbdate.return_value = "2026-03-15"
    entry = _meal_entry_factory(items=[_cook_event_meal_item(portions=2.0)])
    mock_repo.get_meal_entry_by_id_and_user_id.return_value = entry
    mock_repo.get_cook_event_by_id.return_value = _cook_event_with_macros(event_id=8)
    mock_repo.get_active_recipe_by_id.return_value = mock_recipe
    mock_repo.get_cook_event_availability.return_value = ("2026-02-20", 10.0)

    result = update_meal_entry(
        1,
        1,
        items=[{"source": "cook_event", "cook_event_id": 8, "portions": 2}],
    )

    assert result.status == FoodOperationStatus.EXPIRED_COOK_EVENT
    mock_repo.update_meal_entry.assert_not_called()


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_meal_entry_not_found(mock_repo):
    mock_repo.get_meal_entry_by_id_and_user_id.return_value = None

    result = update_meal_entry(1, 1, eaten_at="2026-03-16T08:00")

    assert result.status == FoodOperationStatus.NOT_FOUND
    mock_repo.update_meal_entry.assert_not_called()


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_update_meal_entry_invalid_meal_type(mock_repo):
    mock_repo.get_meal_entry_by_id_and_user_id.return_value = _meal_entry_factory()

    result = update_meal_entry(1, 1, meal_type="brunch")

    assert result.status == FoodOperationStatus.INVALID_MEAL_TYPE
    mock_repo.update_meal_entry.assert_not_called()


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_delete_meal_entry(mock_repo):
    entry = _meal_entry_factory()
    mock_repo.get_meal_entry_by_id_and_user_id.return_value = entry

    result = delete_meal_entry(1, 1)

    assert result.status == FoodOperationStatus.OK
    assert result.meal_entry is entry
    mock_repo.delete_meal_entry.assert_called_once_with(1)


@pytest.mark.unit
@patch("modules.food.service.repository")
def test_delete_meal_entry_not_found(mock_repo):
    mock_repo.get_meal_entry_by_id_and_user_id.return_value = None

    result = delete_meal_entry(1, 1)

    assert result.status == FoodOperationStatus.NOT_FOUND
    mock_repo.delete_meal_entry.assert_not_called()
