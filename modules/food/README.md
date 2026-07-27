# food

Domain module for household food management: ingredient catalog with macros, stock tracking, purchase logging, recipes, and cooking.

## Public API

```python
def create_ingredient(name: str, category: str | None, unit: str, macros: dict, external_source: str | None = None, external_id: str | None = None) -> FoodOperationResult

def update_ingredient(ingredient_id: int, name: str | None = None, category: str | None = None, unit: str | None = None, macros: dict | None = None) -> FoodOperationResult

def delete_ingredient(ingredient_id: int) -> FoodOperationResult

def get_ingredient(ingredient_id: int) -> FoodOperationResult

def list_ingredients(category: str | None = None) -> list[Ingredient]

def set_stock(ingredient_id: int, quantity: float, min_alert_quantity: float = 0.0, expiration_date: str | None = None) -> FoodOperationResult

def get_stock() -> list[IngredientStock]

def get_low_stock() -> list[IngredientStock]

def get_expiring_soon(days: int = 7) -> list[IngredientStock]

def register_purchase(ingredient_id: int, quantity: float, price: int, purchased_at: str, notes: str | None = None) -> FoodOperationResult

def list_purchases(ingredient_id: int | None = None, from_date: str | None = None, to_date: str | None = None) -> list[IngredientPurchase]

def create_recipe(name: str, portions: int, ingredients: list[dict], description: str | None = None, steps: list[str] | None = None) -> FoodOperationResult

def update_recipe(recipe_id: int, name: str | None = None, portions: int | None = None, description: str | None = None, steps: list[str] | None = None, ingredients: list[dict] | None = None) -> FoodOperationResult

def delete_recipe(recipe_id: int) -> FoodOperationResult

def get_recipe(recipe_id: int) -> FoodOperationResult

def list_recipes(ingredient_ids: list[int] | None = None) -> list[Recipe]

def cook_recipe(recipe_id: int, portions_cooked: int, cooked_at: str | None = None) -> CookResult

def compute_recipe_macros(recipe: Recipe) -> RecipeMacros

def suggest_recipes(limit: int = 3, only_with_stock: bool = True) -> SuggestResult

def list_cook_events(recipe_id: int | None = None, from_date: str | None = None, to_date: str | None = None) -> list[CookEvent]
```

## Key types

| Type | Description |
|---|---|
| `Ingredient` | A food ingredient with `name`, `category`, `unit` (`FoodUnit` enum), `macros` (`IngredientMacros`), `external_source`, and `external_id` |
| `IngredientMacros` | Nutrition info per serving: `serving_amount`, `serving_unit` (`FoodUnit`), and optional `kcal`, `protein_g`, `carbs_g`, `fat_g`, `fiber_g` |
| `IngredientStock` | Current stock for an ingredient: `quantity`, `min_alert_quantity`, and `expiration_date` |
| `IngredientPurchase` | A purchase record: `quantity`, `price` (integer, currency-agnostic), `purchased_at`, and `notes` |
| `Recipe` | A household recipe with `name`, `portions`, `description`, `steps`, and list of `RecipeIngredient` |
| `RecipeIngredient` | An ingredient item in a recipe: `ingredient_id`, `quantity`, `unit` (`FoodUnit`), and the resolved `Ingredient` |
| `RecipeMacros` | Computed macros for a recipe: `total` (whole recipe) and `per_portion` (total / portions) |
| `RecipeSummary` | A recipe with its computed `macros` and a `feasible` flag (stock check) |
| `CookEvent` | A logged cooking event: `recipe_id`, `portions` actually cooked, and `cooked_at` |
| `FoodOperationResult` | Result of ingredient/recipe create/update/delete/stock/purchase with optional `ingredient`, `recipe`, `stock`, or `purchase` and `FoodOperationStatus` |
| `CookResult` | Result of `cook_recipe`: `cook_event`, `macros`, `status`, and `missing_ingredient_ids` on insufficient stock |
| `SuggestResult` | Result of `suggest_recipes`: list of `RecipeSummary` and `status` |
| `FoodUnit` | Enum: `G` ("g"), `ML` ("ml"), `UNIT` ("unit"), `TABLESPOON` ("tablespoon") |
| `FoodOperationStatus` | Enum: `OK`, `INVALID_ID`, `INVALID_NAME`, `DUPLICATE_NAME`, `INVALID_UNIT`, `INVALID_MACROS`, `INVALID_QUANTITY`, `INVALID_PRICE`, `INVALID_PORTIONS`, `INSUFFICIENT_STOCK`, `NOT_FOUND`, `EXTERNAL_NOT_FOUND` |
| `ExternalSource` | Enum: `OPENFOODFACTS`, `USDA` |

## Errors

| Error | Description |
|---|---|
| `IngredientAlreadyExistsError` | Raised by repository when creating or updating an ingredient with a duplicate active name |
| `RecipeAlreadyExistsError` | Raised by repository when creating or updating a recipe with a duplicate active name |
| `InsufficientStockError` | Raised when cooking requires more stock than available; carries the list of missing `Ingredient` objects |

## Behavior notes

- **Macros validation**: `serving_amount` must be > 0, `serving_unit` must be a valid `FoodUnit` value matching the ingredient's `unit`. Nutrient values are optional non-negative numbers.
- **Unit enforcement**: recipe ingredients must use the same `FoodUnit` as the ingredient they reference. Cross-unit conversions are not supported in MVP.
- **Soft-delete ingredients**: sets `deleted_at` timestamp and zeroes out `food_stock.quantity` in cascade. Historical recipes still reference the deleted ingredient (ghost data).
- **Cook recipe is transactional**: stock validation and decrement happen in a single SQLite connection with rollback on `InsufficientStockError`.
- **Stock on purchase**: `register_purchase` automatically increments `food_stock.quantity` (upserts if no stock row exists).
- **Recipe macros are computed**, not persisted: `compute_recipe_macros` sums ingredient macros proportionally to the recipe's declared portions.
- **Only one stock row per ingredient** (unique index on `ingredient_id`).
- **Recipes are global** to the household; no per-user cook logs. Any authenticated user can CRUD.

## Dependencies

- `core/` for DB connection, date utilities, string utilities, and `float_or_none` parser
- Does NOT import from `apps/`
