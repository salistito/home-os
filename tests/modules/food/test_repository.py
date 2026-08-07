import pytest

import modules.food.repository as repository
from modules.food.types import (
    FoodUnit,
    IngredientMacros,
    MealEntryItem,
    MealItemSource,
    MealType,
)

_MACROS = IngredientMacros(
    serving_amount=100,
    serving_unit=FoodUnit.G,
    kcal=250,
    protein_g=26,
    carbs_g=0,
    fat_g=15,
    fiber_g=0,
)
_D = "2026-03-15"
_ARROZ_ARGS = ("Arroz", "granos", FoodUnit.G, _MACROS, _D, _D)
_POLLO_CARNE_ARGS = ("Pollo", "carnes", FoodUnit.G, _MACROS, _D, _D)


@pytest.mark.integration
def test_create_and_get_ingredient(db, frozen_today):
    ing = repository.create_ingredient(
        "Pechuga de pollo", "carnes", FoodUnit.G, _MACROS, "2026-03-15", "2026-03-15"
    )

    assert ing.name == "Pechuga de pollo"
    assert ing.category == "carnes"
    assert ing.unit == "g"
    assert ing.macros.kcal == 250


@pytest.mark.integration
def test_get_active_ingredient_by_name(db, frozen_today):
    repository.create_ingredient(
        "Pechuga de pollo", "carnes", FoodUnit.G, _MACROS, "2026-03-15", "2026-03-15"
    )
    found = repository.get_active_ingredient_by_name("Pechuga de pollo")

    assert found is not None
    assert found.name == "Pechuga de pollo"


@pytest.mark.integration
def test_get_active_ingredient_by_name_not_found(db):
    found = repository.get_active_ingredient_by_name("Nonexistent")

    assert found is None


@pytest.mark.integration
def test_get_active_ingredient_by_id_not_found(db):
    found = repository.get_active_ingredient_by_id(9999)

    assert found is None


@pytest.mark.integration
def test_get_active_ingredients(db, frozen_today):
    repository.create_ingredient(*_ARROZ_ARGS)
    repository.create_ingredient("Leche", "lacteos", FoodUnit.ML, _MACROS, _D, _D)

    all_ing = repository.get_active_ingredients()
    assert len(all_ing) == 2

    grains = repository.get_active_ingredients(category="granos")
    assert len(grains) == 1
    assert grains[0].name == "Arroz"


@pytest.mark.integration
def test_update_active_ingredient(db, frozen_today):
    ing = repository.create_ingredient(
        "Pechuga de pollo", "carnes", FoodUnit.G, _MACROS, "2026-03-15", "2026-03-15"
    )
    result = repository.update_active_ingredient(ing.id, name="Pollo entero", category="aves")

    assert result is True
    updated = repository.get_active_ingredient_by_id(ing.id)
    assert updated.name == "Pollo entero"
    assert updated.category == "aves"


@pytest.mark.integration
def test_soft_delete_active_ingredient(db, frozen_today):
    ing = repository.create_ingredient(
        "Pechuga de pollo", "carnes", FoodUnit.G, _MACROS, "2026-03-15", "2026-03-15"
    )
    repository.upsert_stock(ing.id, 500, 100, None, "2026-03-15")
    repository.soft_delete_active_ingredient(ing.id)

    deleted = repository.get_active_ingredient_by_id(ing.id)
    assert deleted is None

    stock = repository.get_stock_by_ingredient_id(ing.id)
    assert stock.quantity == 0


@pytest.mark.integration
def test_upsert_stock_create(db, frozen_today):
    ing = repository.create_ingredient(
        "Pechuga de pollo", "carnes", FoodUnit.G, _MACROS, "2026-03-15", "2026-03-15"
    )
    stock = repository.upsert_stock(ing.id, 500, 100, None, "2026-03-15")

    assert stock is not None
    assert stock.quantity == 500
    assert stock.min_alert_quantity == 100


@pytest.mark.integration
def test_upsert_stock_update(db, frozen_today):
    ing = repository.create_ingredient(
        "Pechuga de pollo", "carnes", FoodUnit.G, _MACROS, "2026-03-15", "2026-03-15"
    )
    repository.upsert_stock(ing.id, 500, 100, None, "2026-03-15")
    stock = repository.upsert_stock(ing.id, 300, 50, None, "2026-03-16")

    assert stock.quantity == 300


@pytest.mark.integration
def test_adjust_stock(db, frozen_today):
    ing = repository.create_ingredient(
        "Pechuga de pollo", "carnes", FoodUnit.G, _MACROS, "2026-03-15", "2026-03-15"
    )
    repository.upsert_stock(ing.id, 500, 100, None, "2026-03-15")
    stock = repository.adjust_stock(ing.id, -200)

    assert stock.quantity == 300

    stock = repository.adjust_stock(ing.id, 100)
    assert stock.quantity == 400


@pytest.mark.integration
def test_get_stock_filters_deleted_ingredients(db, frozen_today):
    ing = repository.create_ingredient(
        "Pechuga de pollo", "carnes", FoodUnit.G, _MACROS, "2026-03-15", "2026-03-15"
    )
    repository.upsert_stock(ing.id, 500, 100, None, "2026-03-15")

    stock_list = repository.get_stock()
    assert len(stock_list) == 1

    repository.soft_delete_active_ingredient(ing.id)
    stock_list = repository.get_stock()
    assert len(stock_list) == 0


@pytest.mark.integration
def test_get_low_stock(db, frozen_today):
    ing = repository.create_ingredient(
        "Pechuga de pollo", "carnes", FoodUnit.G, _MACROS, "2026-03-15", "2026-03-15"
    )
    repository.upsert_stock(ing.id, 50, 100, None, "2026-03-15")

    low = repository.get_low_stock()
    assert len(low) == 1

    repository.upsert_stock(ing.id, 200, 100, None, "2026-03-15")
    low = repository.get_low_stock()
    assert len(low) == 0


@pytest.mark.integration
def test_create_and_get_purchase(db, frozen_today):
    ing = repository.create_ingredient(
        "Pechuga de pollo", "carnes", FoodUnit.G, _MACROS, "2026-03-15", "2026-03-15"
    )
    purchase = repository.create_purchase(ing.id, 1000, 5990, "2026-03-15", None, "2026-03-15")

    assert purchase is not None
    assert purchase.quantity == 1000
    assert purchase.price == 5990

    purchases = repository.get_purchases(ingredient_id=ing.id)
    assert len(purchases) == 1


@pytest.mark.integration
def test_get_purchases_filtered(db, frozen_today):
    ing = repository.create_ingredient(
        "Pechuga de pollo", "carnes", FoodUnit.G, _MACROS, "2026-03-15", "2026-03-15"
    )
    repository.create_purchase(ing.id, 1000, 5990, "2026-03-10", None, "2026-03-15")
    repository.create_purchase(ing.id, 500, 2990, "2026-03-20", None, "2026-03-15")

    filtered = repository.get_purchases(from_date="2026-03-15", to_date="2026-03-25")
    assert len(filtered) == 1
    assert filtered[0].quantity == 500


@pytest.mark.integration
def test_create_and_get_recipe(db, frozen_today):
    ing = repository.create_ingredient(
        "Pechuga de pollo", "carnes", FoodUnit.G, _MACROS, "2026-03-15", "2026-03-15"
    )
    recipe = repository.create_recipe(
        "Pollo a la plancha", None, None, 4, None, "2026-03-15", "2026-03-15"
    )
    repository.set_recipe_ingredients(recipe.id, [(ing.id, 500, FoodUnit.G)])

    fetched = repository.get_active_recipe_by_id(recipe.id)
    assert fetched is not None
    assert fetched.name == "Pollo a la plancha"
    assert fetched.portions == 4
    assert len(fetched.ingredients) == 1
    assert fetched.ingredients[0].quantity == 500
    assert fetched.ingredients[0].ingredient is not None
    assert fetched.ingredients[0].ingredient.name == "Pechuga de pollo"


@pytest.mark.integration
def test_get_active_recipe_by_name(db, frozen_today):
    repository.create_recipe("Pollo a la plancha", None, None, 4, None, "2026-03-15", "2026-03-15")
    found = repository.get_active_recipe_by_name("Pollo a la plancha")

    assert found is not None


@pytest.mark.integration
def test_get_active_recipes(db, frozen_today):
    repository.create_recipe("Receta A", None, None, 2, None, "2026-03-15", "2026-03-15")
    repository.create_recipe("Receta B", None, None, 4, None, "2026-03-15", "2026-03-15")

    recipes = repository.get_active_recipes()
    assert len(recipes) == 2


@pytest.mark.integration
def test_update_active_recipe(db, frozen_today):
    recipe = repository.create_recipe(
        "Pollo a la plancha", None, None, 4, None, "2026-03-15", "2026-03-15"
    )
    result = repository.update_active_recipe(recipe.id, name="Pollo al horno", portions=6)

    assert result is True
    updated = repository.get_active_recipe_by_id(recipe.id)
    assert updated.name == "Pollo al horno"
    assert updated.portions == 6


@pytest.mark.integration
def test_soft_delete_active_recipe(db, frozen_today):
    recipe = repository.create_recipe(
        "Pollo a la plancha", None, None, 4, None, "2026-03-15", "2026-03-15"
    )
    repository.soft_delete_active_recipe(recipe.id)

    deleted = repository.get_active_recipe_by_id(recipe.id)
    assert deleted is None


@pytest.mark.integration
def test_get_suggested_recipes(db, frozen_today):
    ing1 = repository.create_ingredient(
        "Pechuga de pollo", "carnes", FoodUnit.G, _MACROS, "2026-03-15", "2026-03-15"
    )
    ing2 = repository.create_ingredient(*_ARROZ_ARGS)

    recipe = repository.create_recipe(
        "Pollo con arroz", None, None, 4, None, "2026-03-15", "2026-03-16"
    )
    repository.set_recipe_ingredients(
        recipe.id, [(ing1.id, 500, FoodUnit.G), (ing2.id, 300, FoodUnit.G)]
    )

    repository.upsert_stock(ing1.id, 600, 0, None, "2026-03-15")
    repository.upsert_stock(ing2.id, 400, 0, None, "2026-03-15")

    suggested = repository.get_suggested_recipes(None, 5)
    assert len(suggested) == 1

    # Make stock insufficient for ing1
    repository.upsert_stock(ing1.id, 400, 0, None, "2026-03-15")
    suggested = repository.get_suggested_recipes(None, 5)
    assert len(suggested) == 0


@pytest.mark.integration
def test_get_suggested_recipes_no_ingredients(db, frozen_today):
    repository.create_recipe("Agua hervida", None, None, 1, None, "2026-03-15", "2026-03-15")

    suggested = repository.get_suggested_recipes(None, 5)
    assert len(suggested) == 1
    assert suggested[0].name == "Agua hervida"


@pytest.mark.integration
def test_get_suggested_recipes_with_category(db, frozen_today):
    repository.create_recipe("Desayuno", "desayuno", None, 1, None, "2026-03-15", "2026-03-15")
    repository.create_recipe("Almuerzo", "almuerzo", None, 1, None, "2026-03-15", "2026-03-15")

    suggested = repository.get_suggested_recipes("desayuno", 5)
    assert len(suggested) == 1
    assert suggested[0].name == "Desayuno"


@pytest.mark.integration
def test_get_suggested_recipes_with_category_and_stock(db, frozen_today):
    ing = repository.create_ingredient(
        "Pollo", "carnes", FoodUnit.G, _MACROS, "2026-03-15", "2026-03-15"
    )
    repository.upsert_stock(ing.id, 500, 0, None, "2026-03-15")
    repository.create_recipe(
        "Pollo salteado",
        "almuerzo",
        None,
        1,
        None,
        "2026-03-15",
        "2026-03-15",
    )
    repository.set_recipe_ingredients(
        repository.get_active_recipe_by_name("Pollo salteado").id,
        [(ing.id, 200, FoodUnit.G)],
    )

    suggested = repository.get_suggested_recipes("almuerzo", 5, only_with_stock=True)
    assert len(suggested) == 1


@pytest.mark.integration
def test_create_and_get_cook_events(db, db_user, frozen_today):
    recipe = repository.create_recipe(
        "Pollo a la plancha", None, None, 4, None, "2026-03-15", "2026-03-15"
    )
    event = repository.create_cook_event(recipe.id, db_user.id, 2, "2026-03-15", "2026-03-15")

    assert event is not None
    assert event.recipe_id == recipe.id
    assert event.portions == 2
    assert event.macros is not None
    assert event.ingredients == []
    assert event.consumed_portions == 0.0

    events = repository.get_cook_events()
    assert len(events) == 1


@pytest.mark.integration
def test_get_cook_events_filtered(db, db_user, frozen_today):
    recipe = repository.create_recipe(
        "Pollo a la plancha", None, None, 4, None, "2026-03-15", "2026-03-15"
    )
    repository.create_cook_event(recipe.id, db_user.id, 2, "2026-03-10", "2026-03-15")
    repository.create_cook_event(recipe.id, db_user.id, 2, "2026-03-20", "2026-03-15")

    events = repository.get_cook_events(recipe_id=recipe.id, from_date="2026-03-15")
    assert len(events) == 1
    assert events[0].cooked_at == "2026-03-20"

    events = repository.get_cook_events(to_date="2026-03-15")
    assert len(events) == 1
    assert events[0].cooked_at == "2026-03-10"


@pytest.mark.integration
def test_get_recipe_ids_by_ingredient_ids(db, frozen_today):
    ing1 = repository.create_ingredient(
        "Pechuga de pollo", "carnes", FoodUnit.G, _MACROS, "2026-03-15", "2026-03-15"
    )
    ing2 = repository.create_ingredient(*_ARROZ_ARGS)
    recipe = repository.create_recipe(
        "Pollo con arroz", None, None, 4, None, "2026-03-15", "2026-03-15"
    )
    repository.set_recipe_ingredients(recipe.id, [(ing1.id, 500, FoodUnit.G)])

    ids = repository.get_recipe_ids_by_ingredient_ids([ing1.id])
    assert recipe.id in ids

    ids = repository.get_recipe_ids_by_ingredient_ids([ing2.id])
    assert recipe.id not in ids


@pytest.mark.integration
def test_get_expiring_soon(db, frozen_today):
    from datetime import timedelta

    from core.utils.date import to_db_date

    ing = repository.create_ingredient(
        "Leche", "lacteos", FoodUnit.ML, _MACROS, "2026-03-15", "2026-03-15"
    )
    within = to_db_date(frozen_today + timedelta(days=14))
    beyond = to_db_date(frozen_today + timedelta(days=60))
    cutoff_30 = to_db_date(frozen_today + timedelta(days=30))
    repository.upsert_stock(ing.id, 1000, 0, within, "2026-03-15")

    expiring = repository.get_expiring_soon(cutoff_30)
    assert len(expiring) == 1

    repository.upsert_stock(ing.id, 1000, 0, beyond, "2026-03-15")
    expiring = repository.get_expiring_soon(cutoff_30)
    assert len(expiring) == 0


@pytest.mark.integration
def test_update_active_ingredient_with_macros(db, frozen_today):
    ing = repository.create_ingredient(
        "Pechuga de pollo", "carnes", FoodUnit.G, _MACROS, "2026-03-15", "2026-03-15"
    )
    new_macros = IngredientMacros(
        serving_amount=100,
        serving_unit="g",
        kcal=300,
        protein_g=26,
        carbs_g=0,
        fat_g=15,
        fiber_g=0,
    )
    result = repository.update_active_ingredient(ing.id, macros=new_macros)

    assert result is True
    updated = repository.get_active_ingredient_by_id(ing.id)
    assert updated.macros.kcal == 300


@pytest.mark.integration
def test_update_active_ingredient_no_fields(db, frozen_today):
    ing = repository.create_ingredient(
        "Pechuga de pollo", "carnes", FoodUnit.G, _MACROS, "2026-03-15", "2026-03-15"
    )
    result = repository.update_active_ingredient(ing.id)

    assert result is True
    updated = repository.get_active_ingredient_by_id(ing.id)
    assert updated.name == "Pechuga de pollo"


@pytest.mark.integration
def test_update_active_recipe_no_fields(db, frozen_today):
    recipe = repository.create_recipe(
        "Pollo a la plancha", None, None, 4, None, "2026-03-15", "2026-03-15"
    )
    result = repository.update_active_recipe(recipe.id)

    assert result is True
    updated = repository.get_active_recipe_by_id(recipe.id)
    assert updated.name == "Pollo a la plancha"


@pytest.mark.integration
def test_update_active_recipe_with_steps(db, frozen_today):
    recipe = repository.create_recipe(
        "Pollo a la plancha", None, None, 4, None, "2026-03-15", "2026-03-15"
    )
    result = repository.update_active_recipe(recipe.id, steps=["paso 1", "paso 2"])

    assert result is True
    updated = repository.get_active_recipe_by_id(recipe.id)
    assert updated.steps == ["paso 1", "paso 2"]


@pytest.mark.integration
def test_update_active_recipe_with_description(db, frozen_today):
    recipe = repository.create_recipe(
        "Pollo a la plancha", None, None, 4, ["paso 1"], "2026-03-15", "2026-03-15"
    )
    result = repository.update_active_recipe(recipe.id, description="Delicioso pollo")

    assert result is True
    updated = repository.get_active_recipe_by_id(recipe.id)
    assert updated.description == "Delicioso pollo"
    assert updated.steps == ["paso 1"]


@pytest.mark.integration
def test_get_recipe_ids_by_ingredient_ids_empty(db):
    ids = repository.get_recipe_ids_by_ingredient_ids([])
    assert ids == []


@pytest.mark.integration
def test_get_purchase_by_id_not_found(db):
    purchase = repository.get_purchase_by_id(9999)
    assert purchase is None


@pytest.mark.integration
def test_create_ingredient_duplicate(db, frozen_today):
    from modules.food.errors import IngredientAlreadyExistsError

    repository.create_ingredient(*_ARROZ_ARGS)
    with pytest.raises(IngredientAlreadyExistsError):
        repository.create_ingredient(*_ARROZ_ARGS)


@pytest.mark.integration
def test_create_recipe_duplicate(db, frozen_today):
    from modules.food.errors import RecipeAlreadyExistsError

    repository.create_recipe("Pollo", None, None, 2, None, "2026-03-15", "2026-03-15")
    with pytest.raises(RecipeAlreadyExistsError):
        repository.create_recipe("Pollo", None, None, 4, None, "2026-03-15", "2026-03-16")


@pytest.mark.integration
def test_update_active_ingredient_duplicate_name(db, frozen_today):
    from modules.food.errors import IngredientAlreadyExistsError

    repository.create_ingredient(*_ARROZ_ARGS)
    ing2 = repository.create_ingredient(*_POLLO_CARNE_ARGS)
    with pytest.raises(IngredientAlreadyExistsError):
        repository.update_active_ingredient(ing2.id, name="Arroz")


@pytest.mark.integration
def test_update_active_recipe_duplicate_name(db, frozen_today):
    from modules.food.errors import RecipeAlreadyExistsError

    repository.create_recipe("Pollo", None, None, 2, None, "2026-03-15", "2026-03-15")
    recipe2 = repository.create_recipe("Arroz", None, None, 4, None, "2026-03-15", "2026-03-15")
    with pytest.raises(RecipeAlreadyExistsError):
        repository.update_active_recipe(recipe2.id, name="Pollo")


@pytest.mark.integration
def test_update_active_ingredient_invalid_column(db, frozen_today):
    ing = repository.create_ingredient(*_ARROZ_ARGS)
    with pytest.raises(ValueError):
        repository.update_active_ingredient(ing.id, unknown="x")


@pytest.mark.integration
def test_update_active_recipe_invalid_column(db, frozen_today):
    recipe = repository.create_recipe("Pollo", None, None, 2, None, "2026-03-15", "2026-03-15")
    with pytest.raises(ValueError):
        repository.update_active_recipe(recipe.id, unknown="x")


@pytest.mark.integration
def test_get_cook_event_recipe_ids_since_category(db, db_user, frozen_today):
    desayuno = repository.create_recipe(
        "Desayuno", "desayuno", None, 1, None, "2026-03-15", "2026-03-15"
    )
    almuerzo = repository.create_recipe(
        "Almuerzo", "almuerzo", None, 1, None, "2026-03-15", "2026-03-15"
    )
    repository.create_cook_event(desayuno.id, db_user.id, 1, "2026-03-15", "2026-03-15")
    repository.create_cook_event(almuerzo.id, db_user.id, 1, "2026-03-15", "2026-03-15")

    ids = repository.get_cook_event_recipe_ids_since("2026-03-01", category="desayuno")
    assert desayuno.id in ids
    assert almuerzo.id not in ids


# -- Meal entries --


def _meal_item(
    source=MealItemSource.MANUAL,
    name="Cafe",
    cook_event_id=None,
    portions=None,
    macros=None,
):
    return MealEntryItem(
        id=0,
        meal_entry_id=0,
        source=source,
        name=name,
        macros=macros
        if macros is not None
        else {"kcal": 60.0, "protein_g": 2.0, "carbs_g": 10.0, "fat_g": 0.0, "fiber_g": 0.0},
        cook_event_id=cook_event_id,
        portions=portions,
    )


def _create_entry(
    user_id,
    eaten_at,
    meal_type,
    kcal=60.0,
    notes=None,
    items=None,
):
    return repository.create_meal_entry(
        user_id,
        meal_type,
        {"kcal": kcal},
        notes,
        eaten_at,
        eaten_at[:10],
        items if items is not None else [_meal_item()],
    )


@pytest.mark.integration
def test_create_and_get_meal_entry(db, db_user):
    items = [
        _meal_item(name="Cafe"),
        _meal_item(
            name="Huevos",
            macros={
                "kcal": 140.0,
                "protein_g": 12.0,
                "carbs_g": 1.0,
                "fat_g": 10.0,
                "fiber_g": 0.0,
            },
        ),
    ]
    entry = _create_entry(
        db_user.id,
        "2026-03-15T09:00",
        MealType.BREAKFAST,
        kcal=200.0,
        notes="antes de salir",
        items=items,
    )

    assert entry.id is not None
    assert entry.user_id == db_user.id
    assert entry.user_name == "Test user"
    assert entry.meal_type == MealType.BREAKFAST
    assert entry.macros["kcal"] == 200.0
    assert entry.notes == "antes de salir"
    assert len(entry.items) == 2
    assert entry.items[0].name == "Cafe"
    assert entry.items[0].source == MealItemSource.MANUAL
    assert entry.items[1].macros["protein_g"] == 12.0


@pytest.mark.integration
def test_get_meal_entry_scoped_to_user(db, db_user, db_second_user):
    entry = _create_entry(db_user.id, "2026-03-15T09:00", MealType.LUNCH, kcal=100.0)

    own = repository.get_meal_entry_by_id_and_user_id(entry.id, db_user.id)
    assert own is not None

    other = repository.get_meal_entry_by_id_and_user_id(entry.id, db_second_user.id)
    assert other is None


@pytest.mark.integration
def test_get_meal_entry_not_found(db, db_user):
    entry = repository.get_meal_entry_by_id_and_user_id(9999, db_user.id)
    assert entry is None


@pytest.mark.integration
def test_list_meal_entries_with_date_filter(db, db_user):
    _create_entry(db_user.id, "2026-03-14T12:00", MealType.LUNCH, kcal=300.0)
    _create_entry(db_user.id, "2026-03-15T09:00", MealType.BREAKFAST, kcal=200.0)
    _create_entry(db_user.id, "2026-03-16T20:00", MealType.DINNER, kcal=400.0)

    all_entries = repository.get_meal_entries(db_user.id)
    assert len(all_entries) == 3

    filtered = repository.get_meal_entries(db_user.id, from_date="2026-03-15", to_date="2026-03-15")
    assert len(filtered) == 1
    assert filtered[0].eaten_at == "2026-03-15T09:00"

    day_entries = repository.get_meal_entries(
        db_user.id, from_date="2026-03-15", to_date="2026-03-16"
    )
    assert len(day_entries) == 2


@pytest.mark.integration
def test_list_meal_entries_only_own(db, db_user, db_second_user):
    _create_entry(db_user.id, "2026-03-15T09:00", MealType.BREAKFAST, kcal=200.0)
    _create_entry(db_second_user.id, "2026-03-15T13:00", MealType.LUNCH, kcal=500.0)

    entries = repository.get_meal_entries(db_user.id)
    assert len(entries) == 1
    assert entries[0].user_id == db_user.id


@pytest.mark.integration
def test_update_meal_entry_fields(db, db_user):
    entry = _create_entry(
        db_user.id, "2026-03-15T09:00", MealType.BREAKFAST, kcal=200.0, notes="nota"
    )
    result = repository.update_meal_entry(
        entry.id,
        eaten_at="2026-03-16T08:00",
        meal_type=MealType.LUNCH,
        macros={"kcal": 350.0},
        notes="nueva",
    )

    assert result is True
    updated = repository.get_meal_entry_by_id_and_user_id(entry.id, db_user.id)
    assert updated.eaten_at == "2026-03-16T08:00"
    assert updated.meal_type == MealType.LUNCH
    assert updated.macros["kcal"] == 350.0
    assert updated.notes == "nueva"
    assert len(updated.items) == 1


@pytest.mark.integration
def test_update_meal_entry_items(db, db_user):
    entry = _create_entry(db_user.id, "2026-03-15T09:00", MealType.BREAKFAST)
    new_items = [
        _meal_item(
            name="Pan",
            macros={
                "kcal": 150.0,
                "protein_g": 4.0,
                "carbs_g": 28.0,
                "fat_g": 1.0,
                "fiber_g": 2.0,
            },
        )
    ]

    result = repository.update_meal_entry(entry.id, items=new_items)

    assert result is True
    updated = repository.get_meal_entry_by_id_and_user_id(entry.id, db_user.id)
    assert len(updated.items) == 1
    assert updated.items[0].name == "Pan"


@pytest.mark.integration
def test_update_meal_entry_no_fields(db, db_user):
    entry = _create_entry(db_user.id, "2026-03-15T09:00", MealType.BREAKFAST)
    result = repository.update_meal_entry(entry.id)
    assert result is True


@pytest.mark.integration
def test_update_meal_entry_invalid_column(db, db_user):
    entry = _create_entry(db_user.id, "2026-03-15T09:00", MealType.BREAKFAST)
    with pytest.raises(ValueError):
        repository.update_meal_entry(entry.id, unknown="x")


@pytest.mark.integration
def test_delete_meal_entry_cascades_items(db, db_user):
    entry = _create_entry(
        db_user.id,
        "2026-03-15T09:00",
        MealType.BREAKFAST,
        items=[_meal_item(), _meal_item(name="Tostada")],
    )
    repository.delete_meal_entry(entry.id)

    assert repository.get_meal_entry_by_id_and_user_id(entry.id, db_user.id) is None
    count = db.execute(
        "SELECT COUNT(*) AS c FROM food_meal_entry_items WHERE meal_entry_id = ?", (entry.id,)
    ).fetchone()["c"]
    assert count == 0


@pytest.mark.integration
def test_create_meal_entry_cook_event_item(db, db_user):
    recipe = repository.create_recipe("Pollo", None, None, 4, None, "2026-03-15", "2026-03-15")
    event = repository.create_cook_event(recipe.id, db_user.id, 4, "2026-03-15", "2026-03-15")
    item = _meal_item(
        source=MealItemSource.COOK_EVENT,
        name="Pollo",
        cook_event_id=event.id,
        portions=2.0,
        macros={"kcal": 1000.0, "protein_g": 80.0, "carbs_g": 0.0, "fat_g": 40.0, "fiber_g": 0.0},
    )
    entry = _create_entry(
        db_user.id,
        "2026-03-15T13:00",
        MealType.LUNCH,
        kcal=1000.0,
        items=[item],
    )

    loaded = repository.get_meal_entry_by_id_and_user_id(entry.id, db_user.id)
    assert loaded.items[0].cook_event_id == event.id
    assert loaded.items[0].portions == 2.0
    assert loaded.items[0].macros["kcal"] == 1000.0


@pytest.mark.integration
def test_get_cook_event_availability(db, db_user):
    recipe = repository.create_recipe("Pollo", None, None, 4, None, "2026-03-15", "2026-03-15")
    event = repository.create_cook_event(recipe.id, db_user.id, 4, "2026-03-15", "2026-03-15")
    cook_item = lambda portions: _meal_item(  # noqa: E731
        source=MealItemSource.COOK_EVENT,
        name="Pollo",
        cook_event_id=event.id,
        portions=portions,
        macros={"kcal": 1000.0, "protein_g": 80.0, "carbs_g": 0.0, "fat_g": 40.0, "fiber_g": 0.0},
    )
    first = _create_entry(
        db_user.id, "2026-03-15T13:00", MealType.LUNCH, kcal=1000.0, items=[cook_item(1.5)]
    )
    _create_entry(
        db_user.id, "2026-03-16T13:00", MealType.LUNCH, kcal=1000.0, items=[cook_item(2)]
    )

    assert repository.get_cook_event_availability(event.id) == ("2026-03-15", 0.5)
    assert repository.get_cook_event_availability(
        event.id, exclude_meal_entry_id=first.id
    ) == ("2026-03-15", 2.0)
    assert repository.get_cook_event_availability(9999) is None


@pytest.mark.integration
def test_get_cook_events_includes_consumed_portions(db, db_user):
    recipe = repository.create_recipe("Pollo", None, None, 4, None, "2026-03-15", "2026-03-15")
    event = repository.create_cook_event(recipe.id, db_user.id, 4, "2026-03-15", "2026-03-15")
    item = _meal_item(
        source=MealItemSource.COOK_EVENT,
        name="Pollo",
        cook_event_id=event.id,
        portions=2.5,
        macros={"kcal": 1000.0, "protein_g": 80.0, "carbs_g": 0.0, "fat_g": 40.0, "fiber_g": 0.0},
    )
    _create_entry(db_user.id, "2026-03-15T13:00", MealType.LUNCH, kcal=1000.0, items=[item])

    events = repository.get_cook_events()
    assert len(events) == 1
    assert events[0].consumed_portions == 2.5
    assert events[0].portions - events[0].consumed_portions == 1.5
