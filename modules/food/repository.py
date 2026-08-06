import json
import sqlite3

from core.db import get_connection
from core.utils.date import get_today, to_db_date
from core.utils.string import normalize_string
from modules.food.errors import (
    IngredientAlreadyExistsError,
    InsufficientStockError,
    RecipeAlreadyExistsError,
)
from modules.food.types import (
    CookEvent,
    CookEventIngredient,
    FoodNutritionGoals,
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

_INGREDIENT_COLUMNS = (
    "id, name, category, unit, macros, purchase_unit, purchase_conversion_factor, "
    "external_source, external_id, created_at, updated_at, deleted_at"
)
_INGREDIENT_STOCK_COLUMNS = (
    "id, ingredient_id, quantity, min_alert_quantity, expiration_date, updated_at"
)
_INGREDIENT_PURCHASE_COLUMNS = "id, ingredient_id, quantity, price, purchased_at, notes, created_at"
_RECIPE_COLUMNS = (
    "id, name, category, description, portions, steps, created_at, updated_at, deleted_at"
)
_RECIPE_INGREDIENT_COLUMNS = "id, recipe_id, ingredient_id, quantity, unit"
_COOK_EVENT_COLUMNS = (
    "ce.id, ce.recipe_id, ce.user_id, u.name as user_name, "
    "ce.portions, ce.macros, ce.cooked_at, ce.created_at"
)
_NUTRITION_GOALS_COLUMNS = (
    "id, user_id, kcal_target, protein_g_target, carbs_g_target, fat_g_target, updated_at"
)
_MEAL_ENTRY_COLUMNS = (
    "me.id, me.user_id, u.name as user_name, me.meal_type, me.macros, me.notes, "
    "me.eaten_at, me.created_at"
)
_MEAL_ENTRY_ITEM_COLUMNS = "id, meal_entry_id, source, name, macros, cook_event_id, portions"


EDITABLE_INGREDIENT_COLUMNS = {
    "name",
    "category",
    "unit",
    "macros",
    "purchase_unit",
    "purchase_conversion_factor",
    "updated_at",
}

EDITABLE_RECIPE_COLUMNS = {
    "name",
    "category",
    "description",
    "portions",
    "steps",
    "updated_at",
}

EDITABLE_MEAL_ENTRY_COLUMNS = {"meal_type", "macros", "notes", "eaten_at"}


def _row_to_ingredient(row) -> Ingredient:
    return Ingredient(
        row["id"],
        row["name"],
        row["category"],
        FoodUnit(row["unit"]),
        IngredientMacros.from_dict(json.loads(row["macros"])),
        row["purchase_unit"],
        row["purchase_conversion_factor"],
        row["external_source"],
        row["external_id"],
        row["created_at"],
        row["updated_at"],
        row["deleted_at"],
    )


def _row_to_ingredient_stock(row) -> IngredientStock:
    return IngredientStock(
        row["id"],
        row["ingredient_id"],
        row["quantity"],
        row["min_alert_quantity"],
        row["expiration_date"],
        row["updated_at"],
    )


def _row_to_ingredient_purchase(row) -> IngredientPurchase:
    return IngredientPurchase(
        row["id"],
        row["ingredient_id"],
        row["quantity"],
        row["price"],
        row["purchased_at"],
        row["notes"],
        row["created_at"],
    )


def _row_to_recipe(row) -> Recipe:
    return Recipe(
        row["id"],
        row["name"],
        row["category"],
        row["description"],
        row["portions"],
        json.loads(row["steps"]) if row["steps"] else None,
        row["created_at"],
        row["updated_at"],
        row["deleted_at"],
    )


def _row_to_cook_event(row) -> CookEvent:
    macros = None
    if row["macros"]:
        data = json.loads(row["macros"])
        if "total" in data and "per_portion" in data:
            macros = RecipeMacros(total=data["total"], per_portion=data["per_portion"])
        else:
            macros = RecipeMacros(total={}, per_portion={})
    return CookEvent(
        row["id"],
        row["recipe_id"],
        row["user_id"],
        row["user_name"],
        row["portions"],
        macros,
        row["cooked_at"],
        row["created_at"],
    )


def _row_to_cook_event_ingredient(row) -> CookEventIngredient:
    return CookEventIngredient(
        row["id"],
        row["cook_event_id"],
        row["ingredient_id"],
        row["ingredient_name"],
        row["quantity"],
        FoodUnit(row["unit"]),
        IngredientMacros.from_dict(json.loads(row["macros"])) if row["macros"] else None,
    )


def _row_to_nutrition_goals(row) -> FoodNutritionGoals:
    return FoodNutritionGoals(
        row["id"],
        row["user_id"],
        row["kcal_target"],
        row["protein_g_target"],
        row["carbs_g_target"],
        row["fat_g_target"],
        row["updated_at"],
    )


def _row_to_meal_entry(row) -> MealEntry:
    return MealEntry(
        row["id"],
        row["user_id"],
        row["user_name"],
        MealType(row["meal_type"]),
        json.loads(row["macros"]),
        row["notes"],
        row["eaten_at"],
        row["created_at"],
    )


def _row_to_meal_entry_item(row) -> MealEntryItem:
    return MealEntryItem(
        row["id"],
        row["meal_entry_id"],
        MealItemSource(row["source"]),
        row["name"],
        json.loads(row["macros"]),
        row["cook_event_id"],
        row["portions"],
    )


# Ingredients
def create_ingredient(
    name: str,
    category: str | None,
    unit: FoodUnit,
    macros: IngredientMacros,
    created_at: str,
    updated_at: str,
    purchase_unit: str | None = None,
    purchase_conversion_factor: float | None = None,
    external_source: str | None = None,
    external_id: str | None = None,
) -> Ingredient:
    normalized_ingredient_name = normalize_string(name)
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO food_ingredients
                    (name, category, unit, macros, purchase_unit, purchase_conversion_factor,
                     external_source, external_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized_ingredient_name,
                    category,
                    unit.value,
                    json.dumps(macros.to_dict()),
                    purchase_unit,
                    purchase_conversion_factor,
                    external_source,
                    external_id,
                    created_at,
                    updated_at,
                ),
            )
        return get_active_ingredient_by_id(cur.lastrowid)

    except sqlite3.IntegrityError as e:
        ingredient = get_active_ingredient_by_name(normalized_ingredient_name)
        raise IngredientAlreadyExistsError(ingredient) from e


def get_active_ingredient_by_id(ingredient_id: int) -> Ingredient | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_INGREDIENT_COLUMNS}
            FROM food_ingredients
            WHERE id = ?
              AND deleted_at IS NULL
            """,
            (ingredient_id,),
        ).fetchone()
    return _row_to_ingredient(row) if row else None


def get_active_ingredient_by_name(ingredient_name: str) -> Ingredient | None:
    normalized_ingredient_name = normalize_string(ingredient_name)
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_INGREDIENT_COLUMNS}
            FROM food_ingredients
            WHERE name = ?
              AND deleted_at IS NULL
            """,
            (normalized_ingredient_name,),
        ).fetchone()
    return _row_to_ingredient(row) if row else None


def get_active_ingredients(category: str | None = None) -> list[Ingredient]:
    with get_connection() as conn:
        if category:
            rows = conn.execute(
                f"""
                SELECT {_INGREDIENT_COLUMNS}
                FROM food_ingredients
                WHERE category = ?
                  AND deleted_at IS NULL
                ORDER BY name COLLATE NOCASE
                """,
                (category,),
            ).fetchall()
        else:
            rows = conn.execute(
                f"""
                SELECT {_INGREDIENT_COLUMNS}
                FROM food_ingredients
                WHERE deleted_at IS NULL
                ORDER BY name COLLATE NOCASE
                """
            ).fetchall()
    return [_row_to_ingredient(r) for r in rows]


def update_active_ingredient(ingredient_id: int, **fields) -> bool:
    if not fields:
        return True

    invalid = set(fields) - EDITABLE_INGREDIENT_COLUMNS
    if invalid:
        raise ValueError(f"Invalid editable ingredient columns: {', '.join(sorted(invalid))}")

    normalized_fields = fields.copy()
    if "name" in normalized_fields and normalized_fields["name"] is not None:
        normalized_fields["name"] = normalize_string(normalized_fields["name"])
    if "unit" in normalized_fields and normalized_fields["unit"] is not None:
        normalized_fields["unit"] = normalized_fields["unit"].value
    if "macros" in normalized_fields:
        normalized_fields["macros"] = json.dumps(normalized_fields["macros"].to_dict())

    set_clauses: list[str] = []
    params: list = []
    for column, value in normalized_fields.items():
        if value is None:
            set_clauses.append(f"{column} = NULL")
        else:
            set_clauses.append(f"{column} = ?")
            params.append(value)
    params.append(ingredient_id)

    try:
        with get_connection() as conn:
            cur = conn.execute(
                f"""
                UPDATE food_ingredients
                SET {", ".join(set_clauses)}
                WHERE id = ?
                  AND deleted_at IS NULL
                """,
                params,
            )
        return cur.rowcount > 0

    except sqlite3.IntegrityError as e:
        ingredient = get_active_ingredient_by_name(normalized_fields["name"])
        assert ingredient is not None
        raise IngredientAlreadyExistsError(ingredient) from e


def soft_delete_active_ingredient(ingredient_id: int) -> bool:
    deleted_at = to_db_date(get_today())
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE food_ingredients
            SET deleted_at = ?
            WHERE id = ?
              AND deleted_at IS NULL
            """,
            (deleted_at, ingredient_id),
        )
        conn.execute(
            """
            UPDATE food_stock
            SET quantity = 0
            WHERE ingredient_id = ?
            """,
            (ingredient_id,),
        )
    return cur.rowcount > 0


# Ingredients Stock
def upsert_stock(
    ingredient_id: int,
    quantity: float,
    min_alert_quantity: float,
    expiration_date: str | None,
    updated_at: str,
) -> IngredientStock:
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM food_stock WHERE ingredient_id = ?", (ingredient_id,)
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE food_stock
                SET quantity = ?,
                    min_alert_quantity = ?,
                    expiration_date = ?,
                    updated_at = ?
                WHERE ingredient_id = ?
                """,
                (quantity, min_alert_quantity, expiration_date, updated_at, ingredient_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO food_stock
                    (ingredient_id, quantity, min_alert_quantity,
                     expiration_date, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (ingredient_id, quantity, min_alert_quantity, expiration_date, updated_at),
            )
    return get_stock_by_ingredient_id(ingredient_id)


def get_stock_by_ingredient_id(ingredient_id: int) -> IngredientStock | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_INGREDIENT_STOCK_COLUMNS}
            FROM food_stock
            WHERE ingredient_id = ?
            """,
            (ingredient_id,),
        ).fetchone()
    return _row_to_ingredient_stock(row) if row else None


def get_stock() -> list[IngredientStock]:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT s.{", s.".join(_INGREDIENT_STOCK_COLUMNS.split(", "))}
            FROM food_stock s
            JOIN food_ingredients i
              ON i.id = s.ingredient_id
            WHERE i.deleted_at IS NULL
            ORDER BY i.name COLLATE NOCASE
            """
        ).fetchall()
    return [_row_to_ingredient_stock(r) for r in rows]


def get_low_stock() -> list[IngredientStock]:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT s.{", s.".join(_INGREDIENT_STOCK_COLUMNS.split(", "))}
            FROM food_stock s
            JOIN food_ingredients i
              ON i.id = s.ingredient_id
            WHERE s.quantity <= s.min_alert_quantity
               AND i.deleted_at IS NULL
            ORDER BY i.name COLLATE NOCASE
            """
        ).fetchall()
    return [_row_to_ingredient_stock(r) for r in rows]


def get_expiring_soon(cutoff_date: str) -> list[IngredientStock]:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT s.{", s.".join(_INGREDIENT_STOCK_COLUMNS.split(", "))}
            FROM food_stock s
            JOIN food_ingredients i
              ON i.id = s.ingredient_id
            WHERE s.expiration_date IS NOT NULL
               AND s.expiration_date <= ?
               AND i.deleted_at IS NULL
            ORDER BY s.expiration_date ASC
            """,
            (cutoff_date,),
        ).fetchall()
    return [_row_to_ingredient_stock(r) for r in rows]


def adjust_stock(ingredient_id: int, delta: float) -> IngredientStock | None:
    updated_at = to_db_date(get_today())
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM food_stock WHERE ingredient_id = ?", (ingredient_id,)
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE food_stock
                SET quantity = quantity + ?, updated_at = ?
                WHERE ingredient_id = ?
                """,
                (delta, updated_at, ingredient_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO food_stock
                    (ingredient_id, quantity, min_alert_quantity,
                     expiration_date, updated_at)
                VALUES (?, ?, 0, NULL, ?)
                """,
                (ingredient_id, delta, updated_at),
            )
    return get_stock_by_ingredient_id(ingredient_id)


# Ingredients Purchase
def create_purchase(
    ingredient_id: int,
    quantity: float,
    price: int,
    purchased_at: str,
    notes: str | None,
    created_at: str,
) -> IngredientPurchase:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO food_purchases
                (ingredient_id, quantity, price, purchased_at, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (ingredient_id, quantity, price, purchased_at, notes, created_at),
        )
    return get_purchase_by_id(cur.lastrowid)


def get_purchase_by_id(purchase_id: int) -> IngredientPurchase | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_INGREDIENT_PURCHASE_COLUMNS}
            FROM food_purchases
            WHERE id = ?
            """,
            (purchase_id,),
        ).fetchone()
    return _row_to_ingredient_purchase(row) if row else None


def get_purchases(
    ingredient_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list[IngredientPurchase]:
    with get_connection() as conn:
        conditions: list = []
        params: list = []
        if ingredient_id is not None:
            conditions.append("ingredient_id = ?")
            params.append(ingredient_id)
        if from_date:
            conditions.append("purchased_at >= ?")
            params.append(from_date)
        if to_date:
            conditions.append("purchased_at <= ?")
            params.append(to_date)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = conn.execute(
            f"""
            SELECT {_INGREDIENT_PURCHASE_COLUMNS}
            FROM food_purchases
            {where}
            ORDER BY purchased_at DESC
            """,
            params,
        ).fetchall()
    return [_row_to_ingredient_purchase(r) for r in rows]


def delete_purchase(purchase_id: int) -> IngredientPurchase | None:
    purchase = get_purchase_by_id(purchase_id)
    if purchase is None:
        return None
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM food_purchases
            WHERE id = ?
            """,
            (purchase_id,),
        )
    return purchase


# Recipes
def create_recipe(
    name: str,
    category: str | None,
    description: str | None,
    portions: int,
    steps: list[str] | None,
    created_at: str,
    updated_at: str,
) -> Recipe:
    normalized_recipe_name = normalize_string(name)
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """INSERT INTO food_recipes
                       (name, category, description, portions, steps, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    normalized_recipe_name,
                    category,
                    description,
                    portions,
                    json.dumps(steps) if steps else None,
                    created_at,
                    updated_at,
                ),
            )
        return get_active_recipe_by_id(cur.lastrowid)

    except sqlite3.IntegrityError as e:
        recipe = get_active_recipe_by_name(normalized_recipe_name)
        raise RecipeAlreadyExistsError(recipe) from e


def get_active_recipe_by_id(recipe_id: int) -> Recipe | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_RECIPE_COLUMNS}
            FROM food_recipes
            WHERE id = ?
              AND deleted_at IS NULL
            """,
            (recipe_id,),
        ).fetchone()
        if row is None:
            return None
        recipe = _row_to_recipe(row)
        recipe.ingredients = _ingredients_for(conn, [recipe_id]).get(recipe_id, [])
    return recipe


def get_active_recipe_by_name(recipe_name: str) -> Recipe | None:
    normalized_recipe_name = normalize_string(recipe_name)
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_RECIPE_COLUMNS}
            FROM food_recipes
            WHERE name = ?
              AND deleted_at IS NULL
            """,
            (normalized_recipe_name,),
        ).fetchone()
    return _row_to_recipe(row) if row else None


def get_active_recipes(ingredient_ids: list[int] | None = None) -> list[Recipe]:
    with get_connection() as conn:
        params: list = []
        extra = ""
        if ingredient_ids is not None and len(ingredient_ids) > 0:
            placeholders = ",".join("?" * len(ingredient_ids))
            extra = f"""
                  AND id IN (
                    SELECT recipe_id
                    FROM food_recipe_ingredients
                    WHERE ingredient_id IN ({placeholders})
                    GROUP BY recipe_id
                    HAVING COUNT(DISTINCT ingredient_id) = ?
                  )
                """
            params.extend(ingredient_ids)
            params.append(len(ingredient_ids))
        rows = conn.execute(
            f"""
            SELECT {_RECIPE_COLUMNS}
            FROM food_recipes
            WHERE deleted_at IS NULL
            {extra}
            ORDER BY name COLLATE NOCASE
            """,
            params,
        ).fetchall()
        recipes = [_row_to_recipe(r) for r in rows]
        recipe_ids = [r["id"] for r in rows]
        ingredients = _ingredients_for(conn, recipe_ids)
        for recipe in recipes:
            recipe.ingredients = ingredients.get(recipe.id, [])
    return recipes


def get_recipe_ids_by_ingredient_ids(ingredient_ids: list[int]) -> list[int]:
    if not ingredient_ids:
        return []
    placeholders = ",".join("?" * len(ingredient_ids))
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT DISTINCT ri.recipe_id
            FROM food_recipe_ingredients ri
            JOIN food_recipes r
              ON r.id = ri.recipe_id
            WHERE ri.ingredient_id IN ({placeholders})
              AND r.deleted_at IS NULL
            """,
            ingredient_ids,
        ).fetchall()
    return [r["recipe_id"] for r in rows]


def get_suggested_recipes(
    category: str | None,
    limit: int,
    only_with_stock: bool = True,
    order_random: bool = False,
    exclude_recipe_ids: list[int] | None = None,
) -> list[Recipe]:
    category_clause = ""
    exclude_clause = ""
    order = "RANDOM()" if order_random else "updated_at DESC"
    params: list = []
    if exclude_recipe_ids:
        placeholders = ",".join("?" for _ in exclude_recipe_ids)
        exclude_clause = f"AND id NOT IN ({placeholders})"
        params = exclude_recipe_ids + params
    if category:
        category_clause = "AND category = ?"
        params = [category] + params
    params.append(limit)
    with get_connection() as conn:
        if only_with_stock:
            rows = conn.execute(
                f"""
                SELECT {_RECIPE_COLUMNS}
                FROM food_recipes
                WHERE deleted_at IS NULL
                  AND id NOT IN (
                    SELECT ri.recipe_id
                    FROM food_recipe_ingredients ri
                    LEFT JOIN food_stock s
                      ON s.ingredient_id = ri.ingredient_id
                    WHERE COALESCE(s.quantity, 0) < ri.quantity
                  )
                  {category_clause}
                  {exclude_clause}
                ORDER BY {order}
                LIMIT ?
                """,
                params,
            ).fetchall()
        else:
            rows = conn.execute(
                f"""
                SELECT {_RECIPE_COLUMNS}
                FROM food_recipes
                WHERE deleted_at IS NULL
                  {category_clause}
                  {exclude_clause}
                ORDER BY {order}
                LIMIT ?
                """,
                params,
            ).fetchall()
        recipes = [_row_to_recipe(r) for r in rows]
        recipe_ids = [r["id"] for r in rows]
        ingredients = _ingredients_for(conn, recipe_ids)
        for recipe in recipes:
            recipe.ingredients = ingredients.get(recipe.id, [])
    return recipes


def update_active_recipe(recipe_id: int, **fields) -> bool:
    if not fields:
        return True

    invalid = set(fields) - EDITABLE_RECIPE_COLUMNS
    if invalid:
        raise ValueError(f"Invalid editable recipe columns: {', '.join(sorted(invalid))}")

    normalized_fields = fields.copy()
    if "name" in normalized_fields and normalized_fields["name"] is not None:
        normalized_fields["name"] = normalize_string(normalized_fields["name"])
    if "steps" in normalized_fields:
        normalized_fields["steps"] = (
            json.dumps(normalized_fields["steps"]) if normalized_fields["steps"] else None
        )

    set_clauses: list[str] = []
    params: list = []
    for column, value in normalized_fields.items():
        if value is None:
            set_clauses.append(f"{column} = NULL")
        else:
            set_clauses.append(f"{column} = ?")
            params.append(value)
    params.append(recipe_id)

    try:
        with get_connection() as conn:
            cur = conn.execute(
                f"""
                UPDATE food_recipes
                SET {", ".join(set_clauses)}
                WHERE id = ?
                  AND deleted_at IS NULL
                """,
                params,
            )
        return cur.rowcount > 0

    except sqlite3.IntegrityError as e:
        recipe = get_active_recipe_by_name(normalized_fields["name"])
        assert recipe is not None
        raise RecipeAlreadyExistsError(recipe) from e


def set_recipe_ingredients(recipe_id: int, ingredients: list[tuple[int, float, FoodUnit]]) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM food_recipe_ingredients WHERE recipe_id = ?", (recipe_id,))
        conn.executemany(
            """
            INSERT INTO food_recipe_ingredients
                (recipe_id, ingredient_id, quantity, unit)
            VALUES (?, ?, ?, ?)
            """,
            [
                (recipe_id, ingredient_id, quantity, unit.value)
                for ingredient_id, quantity, unit in ingredients
            ],
        )


def soft_delete_active_recipe(recipe_id: int) -> bool:
    deleted_at = to_db_date(get_today())
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE food_recipes
            SET deleted_at = ?
            WHERE id = ?
              AND deleted_at IS NULL
            """,
            (deleted_at, recipe_id),
        )
    return cur.rowcount > 0


def _ingredients_for(conn, recipe_ids: list[int]) -> dict[int, list[RecipeIngredient]]:
    if not recipe_ids:
        return {}
    placeholders = ",".join("?" * len(recipe_ids))
    rows = conn.execute(
        f"""
        SELECT ri.id, ri.recipe_id, ri.ingredient_id, ri.quantity, ri.unit AS recipe_unit,
               i.name, i.category, i.unit AS ingredient_unit, i.macros, i.purchase_unit,
               i.purchase_conversion_factor, i.external_source, i.external_id,
               i.created_at, i.updated_at, i.deleted_at
        FROM food_recipe_ingredients ri
        JOIN food_ingredients i
          ON i.id = ri.ingredient_id
        WHERE ri.recipe_id IN ({placeholders})
        ORDER BY ri.id
        """,
        recipe_ids,
    ).fetchall()
    grouped: dict[int, list[RecipeIngredient]] = {}
    for row in rows:
        ingredient = Ingredient(
            row["ingredient_id"],
            row["name"],
            row["category"],
            FoodUnit(row["ingredient_unit"]),
            IngredientMacros.from_dict(json.loads(row["macros"])),
            row["purchase_unit"],
            row["purchase_conversion_factor"],
            row["external_source"],
            row["external_id"],
            row["created_at"],
            row["updated_at"],
            row["deleted_at"],
        )
        recipe = RecipeIngredient(
            row["id"],
            row["recipe_id"],
            row["ingredient_id"],
            row["quantity"],
            FoodUnit(row["recipe_unit"]),
            ingredient,
        )
        grouped.setdefault(row["recipe_id"], []).append(recipe)
    return grouped


# Cook Event
def create_cook_event(
    recipe_id: int,
    user_id: int,
    portions: int,
    cooked_at: str,
    created_at: str,
) -> CookEvent:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO food_cook_events (recipe_id, user_id, portions, cooked_at, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (recipe_id, user_id, portions, cooked_at, created_at),
        )
    return get_cook_event_by_id(cur.lastrowid)


def _hydrate_cook_event_ingredients(conn, event: CookEvent) -> CookEvent:
    rows = conn.execute(
        """
        SELECT id, cook_event_id, ingredient_id, ingredient_name,
               quantity, unit, macros
        FROM food_cook_event_ingredients
        WHERE cook_event_id = ?
        ORDER BY id
        """,
        (event.id,),
    ).fetchall()
    event.ingredients = [_row_to_cook_event_ingredient(r) for r in rows]
    return event


def _hydrate_cook_events_ingredients(conn, events: list[CookEvent]) -> list[CookEvent]:
    if not events:
        return events
    ids = [e.id for e in events]
    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"""
        SELECT id, cook_event_id, ingredient_id, ingredient_name,
               quantity, unit, macros
        FROM food_cook_event_ingredients
        WHERE cook_event_id IN ({placeholders})
        ORDER BY id
        """,
        ids,
    ).fetchall()
    by_event: dict[int, list[CookEventIngredient]] = {e.id: [] for e in events}
    for row in rows:
        by_event[row["cook_event_id"]].append(_row_to_cook_event_ingredient(row))
    for e in events:
        e.ingredients = by_event[e.id]
    return events


def get_cook_event_by_id(cook_event_id: int) -> CookEvent | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_COOK_EVENT_COLUMNS}
            FROM food_cook_events ce
            JOIN users u ON u.id = ce.user_id
            WHERE ce.id = ?
            """,
            (cook_event_id,),
        ).fetchone()
    if row is None:
        return None
    event = _row_to_cook_event(row)
    with get_connection() as conn:
        _hydrate_cook_event_ingredients(conn, event)
    return event


def get_cook_events(
    recipe_id: int | None = None,
    user_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list[CookEvent]:
    with get_connection() as conn:
        conditions = []
        params: list = []
        if recipe_id is not None:
            conditions.append("ce.recipe_id = ?")
            params.append(recipe_id)
        if user_id is not None:
            conditions.append("ce.user_id = ?")
            params.append(user_id)
        if from_date:
            conditions.append("ce.cooked_at >= ?")
            params.append(from_date)
        if to_date:
            conditions.append("ce.cooked_at <= ?")
            params.append(to_date)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = conn.execute(
            f"""
            SELECT {_COOK_EVENT_COLUMNS}
            FROM food_cook_events ce
            JOIN users u ON u.id = ce.user_id
            {where}
            ORDER BY ce.cooked_at DESC
            """,
            params,
        ).fetchall()
    events = [_row_to_cook_event(r) for r in rows]
    if events:
        with get_connection() as conn:
            _hydrate_cook_events_ingredients(conn, events)
    return events


def get_cook_event_recipe_ids_since(from_date: str, category: str | None = None) -> list[int]:
    category_clause = ""
    params: list = [from_date]
    if category:
        category_clause = "AND r.category = ?"
        params.append(category)
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT ce.recipe_id
            FROM food_cook_events ce
            JOIN food_recipes r
              ON r.id = ce.recipe_id
            WHERE ce.cooked_at >= ?
              AND r.deleted_at IS NULL
              {category_clause}
            ORDER BY ce.cooked_at DESC
            """,
            params,
        ).fetchall()
    return [row["recipe_id"] for row in rows]


def cook_recipe_transactional(
    recipe_id: int,
    user_id: int,
    portions: int,
    macros: RecipeMacros,
    cook_event_ingredients: list[CookEventIngredient],
    cooked_at: str,
    created_at: str,
) -> CookEvent:
    needed_by_id: dict[int, float] = {}
    for cei in cook_event_ingredients:
        needed_by_id[cei.ingredient_id] = needed_by_id.get(cei.ingredient_id, 0.0) + cei.quantity
    with get_connection() as conn:
        missing_ingredients: list[Ingredient] = []
        for ingredient_id, needed_quantity in needed_by_id.items():
            stock = conn.execute(
                "SELECT quantity FROM food_stock WHERE ingredient_id = ?",
                (ingredient_id,),
            ).fetchone()
            if stock is None or stock["quantity"] < needed_quantity:
                ingredient_row = conn.execute(
                    f"SELECT {_INGREDIENT_COLUMNS} FROM food_ingredients WHERE id = ?",
                    (ingredient_id,),
                ).fetchone()
                if ingredient_row:
                    missing_ingredients.append(_row_to_ingredient(ingredient_row))
        if missing_ingredients:
            raise InsufficientStockError(missing_ingredients)
        macros_json = json.dumps({"total": macros.total, "per_portion": macros.per_portion})
        for ingredient_id, needed_quantity in needed_by_id.items():
            conn.execute(
                """
                UPDATE food_stock
                SET quantity = quantity + ?, updated_at = ?
                WHERE ingredient_id = ?
                """,
                (-needed_quantity, to_db_date(get_today()), ingredient_id),
            )
        cur = conn.execute(
            """
            INSERT INTO food_cook_events
                (recipe_id, user_id, portions, macros, cooked_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (recipe_id, user_id, portions, macros_json, cooked_at, created_at),
        )
        event_id = cur.lastrowid
        for cei in cook_event_ingredients:
            cei_macros_json = None
            if cei.macros is not None:
                cei_macros_json = json.dumps(cei.macros.to_dict())
            conn.execute(
                """
                INSERT INTO food_cook_event_ingredients
                    (cook_event_id, ingredient_id, ingredient_name, quantity, unit, macros)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    cei.ingredient_id,
                    cei.ingredient_name,
                    cei.quantity,
                    cei.unit.value,
                    cei_macros_json,
                ),
            )
    return get_cook_event_by_id(event_id)


# Nutrition Goals
def upsert_nutrition_goals(
    user_id: int,
    kcal_target: int | None,
    protein_g_target: float | None,
    carbs_g_target: float | None,
    fat_g_target: float | None,
    updated_at: str,
) -> FoodNutritionGoals:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO food_nutrition_goals
                (user_id, kcal_target, protein_g_target, carbs_g_target,
                 fat_g_target, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                kcal_target = excluded.kcal_target,
                protein_g_target = excluded.protein_g_target,
                carbs_g_target = excluded.carbs_g_target,
                fat_g_target = excluded.fat_g_target,
                updated_at = excluded.updated_at
            """,
            (user_id, kcal_target, protein_g_target, carbs_g_target, fat_g_target, updated_at),
        )
    return get_nutrition_goals(user_id)


def get_nutrition_goals(user_id: int) -> FoodNutritionGoals | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_NUTRITION_GOALS_COLUMNS}
            FROM food_nutrition_goals
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
    return _row_to_nutrition_goals(row) if row else None


# Meal Entries
def _hydrate_meal_entry_items(conn, entry: MealEntry) -> MealEntry:
    rows = conn.execute(
        f"""
        SELECT {_MEAL_ENTRY_ITEM_COLUMNS}
        FROM food_meal_entry_items
        WHERE meal_entry_id = ?
        ORDER BY id
        """,
        (entry.id,),
    ).fetchall()
    entry.items = [_row_to_meal_entry_item(r) for r in rows]
    return entry


def _hydrate_meal_entries_items(conn, entries: list[MealEntry]) -> list[MealEntry]:
    if not entries:
        return entries
    ids = [e.id for e in entries]
    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"""
        SELECT {_MEAL_ENTRY_ITEM_COLUMNS}
        FROM food_meal_entry_items
        WHERE meal_entry_id IN ({placeholders})
        ORDER BY meal_entry_id, id
        """,
        ids,
    ).fetchall()
    by_entry: dict[int, list[MealEntryItem]] = {e.id: [] for e in entries}
    for row in rows:
        by_entry[row["meal_entry_id"]].append(_row_to_meal_entry_item(row))
    for e in entries:
        e.items = by_entry[e.id]
    return entries


def create_meal_entry(
    user_id: int,
    meal_type: MealType,
    macros: dict,
    notes: str | None,
    eaten_at: str,
    created_at: str,
    items: list[MealEntryItem],
) -> MealEntry:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO food_meal_entries
                (user_id, meal_type, macros, notes, eaten_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, meal_type.value, json.dumps(macros), notes, eaten_at, created_at),
        )
        entry_id = cur.lastrowid
        conn.executemany(
            """
            INSERT INTO food_meal_entry_items
                (meal_entry_id, source, name, macros, cook_event_id, portions)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    entry_id,
                    item.source.value,
                    item.name,
                    json.dumps(item.macros),
                    item.cook_event_id,
                    item.portions,
                )
                for item in items
            ],
        )
    return get_meal_entry_by_id_and_user_id(entry_id, user_id)


def get_meal_entry_by_id_and_user_id(entry_id: int, user_id: int) -> MealEntry | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_MEAL_ENTRY_COLUMNS}
            FROM food_meal_entries me
            JOIN users u ON u.id = me.user_id
            WHERE me.id = ?
              AND me.user_id = ?
            """,
            (entry_id, user_id),
        ).fetchone()
        if row is None:
            return None
        entry = _row_to_meal_entry(row)
        _hydrate_meal_entry_items(conn, entry)
    return entry


def get_meal_entries(
    user_id: int,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list[MealEntry]:
    conditions = ["me.user_id = ?"]
    params: list = [user_id]
    if from_date:
        conditions.append("substr(me.eaten_at, 1, 10) >= ?")
        params.append(from_date)
    if to_date:
        conditions.append("substr(me.eaten_at, 1, 10) <= ?")
        params.append(to_date)
    where = "WHERE " + " AND ".join(conditions)
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_MEAL_ENTRY_COLUMNS}
            FROM food_meal_entries me
            JOIN users u ON u.id = me.user_id
            {where}
            ORDER BY me.eaten_at DESC
            """,
            params,
        ).fetchall()
    entries = [_row_to_meal_entry(r) for r in rows]
    if entries:
        with get_connection() as conn:
            _hydrate_meal_entries_items(conn, entries)
    return entries


def update_meal_entry(entry_id: int, **fields) -> bool:
    items = fields.pop("items", None)
    if not fields and items is None:
        return True

    invalid = set(fields) - EDITABLE_MEAL_ENTRY_COLUMNS
    if invalid:
        raise ValueError(f"Invalid editable meal entry columns: {', '.join(sorted(invalid))}")

    normalized_fields = fields.copy()
    if "meal_type" in normalized_fields:
        normalized_fields["meal_type"] = normalized_fields["meal_type"].value
    if "macros" in normalized_fields:
        normalized_fields["macros"] = json.dumps(normalized_fields["macros"])

    set_clauses: list[str] = []
    params: list = []
    for column, value in normalized_fields.items():
        if value is None:
            set_clauses.append(f"{column} = NULL")
        else:
            set_clauses.append(f"{column} = ?")
            params.append(value)
    params.append(entry_id)

    with get_connection() as conn:
        if set_clauses:
            conn.execute(
                f"""
                UPDATE food_meal_entries
                SET {", ".join(set_clauses)}
                WHERE id = ?
                """,
                params,
            )
        if items is not None:
            conn.execute("DELETE FROM food_meal_entry_items WHERE meal_entry_id = ?", (entry_id,))
            conn.executemany(
                """
                INSERT INTO food_meal_entry_items
                    (meal_entry_id, source, name, macros, cook_event_id, portions)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        entry_id,
                        item.source.value,
                        item.name,
                        json.dumps(item.macros),
                        item.cook_event_id,
                        item.portions,
                    )
                    for item in items
                ],
            )
    return True


def delete_meal_entry(entry_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM food_meal_entries WHERE id = ?", (entry_id,))
