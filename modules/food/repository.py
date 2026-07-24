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
    FoodUnit,
    Ingredient,
    IngredientMacros,
    IngredientPurchase,
    IngredientStock,
    Recipe,
    RecipeIngredient,
)

_INGREDIENT_COLUMNS = (
    "id, name, category, unit, macros, external_source,"
    " external_id, created_at, updated_at, deleted_at"
)
_INGREDIENT_STOCK_COLUMNS = (
    "id, ingredient_id, quantity, min_alert_quantity, expiration_date, updated_at"
)
_INGREDIENT_PURCHASE_COLUMNS = "id, ingredient_id, quantity, price, purchased_at, notes, created_at"
_RECIPE_COLUMNS = "id, name, description, portions, steps, created_at, updated_at, deleted_at"
_RECIPE_INGREDIENT_COLUMNS = "id, recipe_id, ingredient_id, quantity, unit"
_COOK_EVENT_COLUMNS = "id, recipe_id, portions, cooked_at, created_at"

EDITABLE_INGREDIENT_COLUMNS = {
    "name",
    "category",
    "unit",
    "macros",
}

EDITABLE_RECIPE_COLUMNS = {
    "name",
    "description",
    "portions",
    "steps",
}


def _row_to_ingredient(row) -> Ingredient:
    return Ingredient(
        row["id"],
        row["name"],
        row["category"],
        FoodUnit(row["unit"]),
        IngredientMacros.from_dict(json.loads(row["macros"])),
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
        row["description"],
        row["portions"],
        json.loads(row["steps"]) if row["steps"] else None,
        row["created_at"],
        row["updated_at"],
        row["deleted_at"],
    )


def _row_to_cook_event(row) -> CookEvent:
    return CookEvent(
        row["id"], row["recipe_id"], row["portions"], row["cooked_at"], row["created_at"]
    )


# Ingredients
def create_ingredient(
    name: str,
    category: str | None,
    unit: FoodUnit,
    macros: IngredientMacros,
    created_at: str,
    updated_at: str,
    external_source: str | None = None,
    external_id: str | None = None,
) -> Ingredient:
    normalized_ingredient_name = normalize_string(name)
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO food_ingredients
                    (name, category, unit, macros, external_source, external_id,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized_ingredient_name,
                    category,
                    unit.value,
                    json.dumps(macros.to_dict()),
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
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE food_stock
            SET quantity = quantity + ?
            WHERE ingredient_id = ?
            """,
            (delta, ingredient_id),
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


# Recipes
def create_recipe(
    name: str,
    portions: int,
    description: str | None,
    steps: list[str] | None,
    created_at: str,
    updated_at: str,
) -> Recipe:
    normalized_recipe_name = normalize_string(name)
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """INSERT INTO food_recipes
                       (name, portions, description, steps, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    normalized_recipe_name,
                    portions,
                    description,
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


def get_suggested_recipes(limit: int, only_with_stock: bool = True) -> list[Recipe]:
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
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                f"""
                SELECT {_RECIPE_COLUMNS}
                FROM food_recipes
                WHERE deleted_at IS NULL
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
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
               i.name, i.category, i.unit AS ingredient_unit, i.macros, i.external_source,
               i.external_id, i.created_at, i.updated_at, i.deleted_at
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
    portions: int,
    cooked_at: str,
    created_at: str,
) -> CookEvent:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO food_cook_events (recipe_id, portions, cooked_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (recipe_id, portions, cooked_at, created_at),
        )
    return get_cook_event_by_id(cur.lastrowid)


def get_cook_event_by_id(cook_event_id: int) -> CookEvent | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_COOK_EVENT_COLUMNS}
            FROM food_cook_events
            WHERE id = ?
            """,
            (cook_event_id,),
        ).fetchone()
    return _row_to_cook_event(row) if row else None


def get_cook_events(
    recipe_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list[CookEvent]:
    with get_connection() as conn:
        conditions = []
        params: list = []
        if recipe_id is not None:
            conditions.append("recipe_id = ?")
            params.append(recipe_id)
        if from_date:
            conditions.append("cooked_at >= ?")
            params.append(from_date)
        if to_date:
            conditions.append("cooked_at <= ?")
            params.append(to_date)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = conn.execute(
            f"""
            SELECT {_COOK_EVENT_COLUMNS}
            FROM food_cook_events
            {where}
            ORDER BY cooked_at DESC
            """,
            params,
        ).fetchall()
    return [_row_to_cook_event(r) for r in rows]


def cook_recipe_transactional(
    recipe_id: int,
    portions: int,
    deltas: list[tuple[int, float]],
    cooked_at: str,
    created_at: str,
) -> CookEvent:
    with get_connection() as conn:
        missing_ingredients: list[Ingredient] = []
        for ingredient_id, needed_quantity in deltas:
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
        for ingredient_id, needed_quantity in deltas:
            conn.execute(
                "UPDATE food_stock SET quantity = quantity - ? WHERE ingredient_id = ?",
                (needed_quantity, ingredient_id),
            )
        cur = conn.execute(
            """
            INSERT INTO food_cook_events (recipe_id, portions, cooked_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (recipe_id, portions, cooked_at, created_at),
        )
    return get_cook_event_by_id(cur.lastrowid)
