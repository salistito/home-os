# food

Domain module for household food management: ingredient catalog with macros, stock tracking, purchase logging, recipes, cooking, and nutrition goals.

## Public API

### Ingredients

```python
def create_ingredient(name: str, category: str | None, unit: str, macros: dict, purchase_unit: str | None = None, purchase_conversion_factor: float | None = None, external_source: str | None = None, external_id: str | None = None) -> FoodOperationResult

def update_ingredient(ingredient_id: int, name: str | None = None, category: str | None = None, unit: str | None = None, macros: dict | None = None, purchase_unit: str | None = None, purchase_conversion_factor: float | None = None) -> FoodOperationResult

def delete_ingredient(ingredient_id: int) -> FoodOperationResult

def get_ingredient(ingredient_id: int) -> FoodOperationResult

def list_ingredients(category: str | None = None) -> list[Ingredient]

def search_ingredient_from_external(name: str, source: str = "openfoodfacts") -> list[dict]

def import_ingredient_from_external(name: str, source: str = "openfoodfacts") -> FoodOperationResult
```

### Stock

```python
def set_stock(ingredient_id: int, quantity: float, unit: str | None = None, min_alert_quantity: float = 0.0, expiration_date: str | None = None) -> FoodOperationResult

def get_stock() -> list[IngredientStock]

def get_low_stock() -> list[IngredientStock]

def get_expiring_soon(days: int = 7) -> list[IngredientStock]
```

### Purchases

```python
def register_purchase(ingredient_id: int, quantity: float, price: int, purchased_at: str, unit: str | None = None, notes: str | None = None) -> FoodOperationResult

def list_purchases(ingredient_id: int | None = None, from_date: str | None = None, to_date: str | None = None) -> list[IngredientPurchase]

def delete_purchase(purchase_id: int) -> FoodOperationResult
```

### Recipes

```python
def create_recipe(name: str, portions: int, ingredients: list[dict], category: str | None = None, description: str | None = None, steps: list[str] | None = None) -> FoodOperationResult

def update_recipe(recipe_id: int, name: str | None = None, category: str | None = None, portions: int | None = None, description: str | None = None, steps: list[str] | None = None, ingredients: list[dict] | None = None) -> FoodOperationResult

def delete_recipe(recipe_id: int) -> FoodOperationResult

def get_recipe(recipe_id: int) -> FoodOperationResult

def list_recipes(ingredient_ids: list[int] | None = None) -> list[Recipe]

def cook_recipe(recipe_id: int, user_id: int, portions_cooked: int, ingredients: list[dict] | None = None, cooked_at: str | None = None) -> CookResult

def compute_recipe_macros(recipe: Recipe) -> RecipeMacros

def list_cook_events(recipe_id: int | None = None, user_id: int | None = None, from_date: str | None = None, to_date: str | None = None) -> list[CookEvent]
```

### Suggestions

```python
def suggest_recipes(user_id: int | None = None, category: str | None = None, limit: int = 3, only_with_stock: bool = True, goal_target: GoalTarget | None = None, variety_days: int = 0) -> SuggestResult
```

### Nutrition Goals

```python
def get_nutrition_goals(user_id: int) -> FoodOperationResult

def update_nutrition_goals(user_id: int, kcal_target: int | None = None, protein_g_target: float | None = None, carbs_g_target: float | None = None, fat_g_target: float | None = None) -> FoodOperationResult
```

## Key types

| Type | Description |
|---|---|
| `Ingredient` | A food ingredient with `name`, `category`, `unit` (`FoodUnit`), `macros` (`IngredientMacros`), optional `purchase_unit`/`purchase_conversion_factor`, `external_source`, and `external_id` |
| `IngredientMacros` | Nutrition info per serving: `serving_amount`, `serving_unit` (`FoodUnit`), and optional `kcal`, `protein_g`, `carbs_g`, `fat_g`, `fiber_g` |
| `IngredientStock` | Current stock for an ingredient: `quantity`, `min_alert_quantity`, and `expiration_date` |
| `IngredientPurchase` | A purchase record: `quantity`, `price` (integer, currency-agnostic), `purchased_at`, and `notes` |
| `Recipe` | A household recipe with `name`, `category`, `portions`, `description`, `steps`, and list of `RecipeIngredient` |
| `RecipeIngredient` | An ingredient item in a recipe: `ingredient_id`, `quantity`, `unit` (`FoodUnit`), and the resolved `Ingredient` |
| `RecipeMacros` | Computed macros for a recipe: `total` (whole recipe) and `per_portion` (total / portions) |
| `RecipeSummary` | A recipe with its computed `macros`, a `feasible` flag (stock check), and a `score` (ranking) |
| `CookEvent` | A logged cooking event with `recipe_id`, `user_id`, `user_name`, `portions`, `macros`, `cooked_at`, and list of `CookEventIngredient` |
| `CookEventIngredient` | An ingredient used in a cook event: `ingredient_id`, `ingredient_name`, `quantity`, `unit`, and scaled `macros` |
| `CookResult` | Result of `cook_recipe`: `cook_event`, `macros`, `status`, and `missing_ingredient_ids` on insufficient stock |
| `SuggestResult` | Result of `suggest_recipes`: list of `RecipeSummary` and `status` |
| `FoodNutritionGoals` | Per-user daily nutrition targets: `kcal_target`, `protein_g_target`, `carbs_g_target`, `fat_g_target` |
| `GoalTarget` | Inline nutrition target used when querying `suggest_recipes` (overrides user's stored goals) |
| `FoodOperationResult` | Generic result for create/update/delete/stock/purchase/goals operations with the relevant entity and `FoodOperationStatus` |
| `FoodUnit` | Enum: `G` ("g"), `ML` ("ml"), `UNIT` ("unit"), `TABLESPOON` ("tablespoon") |
| `FoodOperationStatus` | Enum: `OK`, `INVALID_ID`, `INVALID_NAME`, `DUPLICATE_NAME`, `INVALID_UNIT`, `INVALID_MACROS`, `INVALID_PURCHASE_UNIT`, `INVALID_PURCHASE_CONVERSION_FACTOR`, `INVALID_QUANTITY`, `INVALID_PRICE`, `INVALID_PORTIONS`, `INSUFFICIENT_STOCK`, `CANNOT_REVERT_PURCHASE`, `INVALID_COOK_INGREDIENTS`, `NOT_FOUND`, `EXTERNAL_NOT_FOUND` |
| `ExternalSource` | Enum: `OPENFOODFACTS`, `USDA` |

## Errors

| Error | Description |
|---|---|
| `IngredientAlreadyExistsError` | Raised by repository when creating or updating an ingredient with a duplicate active name |
| `RecipeAlreadyExistsError` | Raised by repository when creating or updating a recipe with a duplicate active name |
| `InsufficientStockError` | Raised when cooking requires more stock than available; carries the list of missing `Ingredient` objects |

## Behavior notes

- **Macros validation**: `serving_amount` must be > 0, `serving_unit` must be a valid `FoodUnit` value matching the ingredient's `unit`. Nutrient values are optional non-negative numbers.
- **Unit enforcement**: recipe ingredients must use the same `FoodUnit` as the ingredient they reference. Cross-unit conversions are not supported in MVP, except via `purchase_unit`/`purchase_conversion_factor` for stock/purchase operations.
- **Purchase unit**: ingredients can declare a `purchase_unit` (e.g. "kg") and `purchase_conversion_factor` (e.g. 1000 for g → kg). When `unit` is provided to `set_stock` or `register_purchase`, it is converted to the ingredient's native `FoodUnit` using this factor before persisting.
- **Soft-delete ingredients**: sets `deleted_at` timestamp and zeroes out `food_stock.quantity` in cascade. Historical recipes still reference the deleted ingredient (ghost data).
- **Cook recipe is transactional**: stock validation and decrement happen in a single SQLite connection with rollback on `InsufficientStockError`. Accepts an optional `ingredients` override list to cook with different quantities/units than the recipe specifies.
- **Stock on purchase**: `register_purchase` automatically increments `food_stock.quantity` (upserts if no stock row exists).
- **Recipe macros are computed**, not persisted: `compute_recipe_macros` sums ingredient macros proportionally to the recipe's declared portions.
- **Cook event macros** are computed at cook time via `modules/food/macros.py` (`compute_cook_event_macros`, `scale_macros`) and persisted alongside the event.
- **Only one stock row per ingredient** (unique index on `ingredient_id`).
- **Recipes are global** to the household. Cook events track which user (`user_id`) performed them.
- **External sources**: `search_ingredient_from_external` queries [OpenFoodFacts](https://world.openfoodfacts.org/) and returns candidate products; `import_ingredient_from_external` picks the first result and creates an ingredient.
- **Suggestions**: `suggest_recipes` filters by stock availability, optionally targets user's stored nutrition goals or an inline `GoalTarget`, and can exclude recently cooked recipes for variety (`variety_days`).
- **Nutrition goals**: stored per-user with optional daily targets for kcal, protein, carbs, and fat. Used by `suggest_recipes` to rank recipes.

## Dependencies

- `core/` for DB connection, date utilities, string utilities, and `float_or_none` parser
- `httpx` for OpenFoodFacts API calls (in `external.py`)
- Does NOT import from `apps/`
