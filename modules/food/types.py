from dataclasses import dataclass, field
from enum import StrEnum

from core.utils.parser import float_or_none

MACROS_KEYS = ("kcal", "protein_g", "carbs_g", "fat_g", "fiber_g")


class FoodUnit(StrEnum):
    G = "g"
    ML = "ml"
    UNIT = "unit"
    TABLESPOON = "tablespoon"


class ExternalSource(StrEnum):
    OPENFOODFACTS = "openfoodfacts"
    USDA = "usda"


class FoodOperationStatus(StrEnum):
    OK = "ok"
    INVALID_ID = "invalid_id"
    INVALID_NAME = "invalid_name"
    DUPLICATE_NAME = "duplicate_name"
    INVALID_UNIT = "invalid_unit"
    INVALID_MACROS = "invalid_macros"
    INVALID_PURCHASE_UNIT = "invalid_purchase_unit"
    INVALID_PURCHASE_CONVERSION_FACTOR = "invalid_purchase_conversion_factor"
    INVALID_QUANTITY = "invalid_quantity"
    INVALID_PRICE = "invalid_price"
    INVALID_PORTIONS = "invalid_portions"
    INSUFFICIENT_STOCK = "insufficient_stock"
    CANNOT_REVERT_PURCHASE = "cannot_revert_purchase"
    INVALID_COOK_INGREDIENTS = "invalid_cook_ingredients"
    NOT_FOUND = "not_found"
    EXTERNAL_NOT_FOUND = "external_not_found"


@dataclass
class IngredientMacros:
    serving_amount: float
    serving_unit: FoodUnit
    kcal: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "IngredientMacros":
        if not isinstance(data, dict):
            raise ValueError("Macros must be a JSON object.")
        serving_amount = data.get("serving_amount")
        if not isinstance(serving_amount, (int, float)) or serving_amount <= 0:
            raise ValueError("serving_amount is required and must be > 0.")
        serving_unit_str = data.get("serving_unit")
        if not isinstance(serving_unit_str, str) or not serving_unit_str.strip():
            raise ValueError("serving_unit is required and must be a non-empty string.")
        try:
            serving_unit = FoodUnit(serving_unit_str)
        except ValueError:
            raise ValueError(f"Invalid serving_unit: '{serving_unit}'.")
        for key in MACROS_KEYS:
            val = data.get(key)
            if val is not None and (not isinstance(val, (int, float)) or val < 0):
                raise ValueError(f"{key} must be a non-negative number.")
        return cls(
            serving_amount=float(serving_amount),
            serving_unit=serving_unit,
            kcal=float_or_none(data.get("kcal")),
            protein_g=float_or_none(data.get("protein_g")),
            carbs_g=float_or_none(data.get("carbs_g")),
            fat_g=float_or_none(data.get("fat_g")),
            fiber_g=float_or_none(data.get("fiber_g")),
        )

    def to_dict(self) -> dict:
        result: dict = {
            "serving_amount": self.serving_amount,
            "serving_unit": self.serving_unit,
        }
        for key in MACROS_KEYS:
            value = getattr(self, key)
            if value is not None:
                result[key] = value
        return result


@dataclass
class Ingredient:
    id: int
    name: str
    category: str | None
    unit: FoodUnit
    macros: IngredientMacros
    purchase_unit: str | None
    purchase_conversion_factor: float | None
    external_source: str | None
    external_id: str | None
    created_at: str
    updated_at: str
    deleted_at: str | None


@dataclass
class IngredientStock:
    id: int
    ingredient_id: int
    quantity: float
    min_alert_quantity: float
    expiration_date: str | None
    updated_at: str


@dataclass
class IngredientPurchase:
    id: int
    ingredient_id: int
    quantity: float
    price: int
    purchased_at: str
    notes: str | None
    created_at: str


@dataclass
class Recipe:
    id: int
    name: str
    category: str | None
    description: str | None
    portions: int
    steps: list[str] | None
    created_at: str
    updated_at: str
    deleted_at: str | None
    ingredients: list["RecipeIngredient"] = field(default_factory=list)


@dataclass
class RecipeIngredient:
    id: int
    recipe_id: int
    ingredient_id: int
    quantity: float
    unit: FoodUnit
    ingredient: Ingredient | None = None


@dataclass
class RecipeMacros:
    total: dict
    per_portion: dict


@dataclass
class RecipeSummary:
    recipe: Recipe
    macros: RecipeMacros
    feasible: bool
    score: float = 0.0


@dataclass
class CookEvent:
    id: int
    recipe_id: int
    user_id: int
    user_name: str
    portions: int
    macros: RecipeMacros | None
    cooked_at: str
    created_at: str
    ingredients: list["CookEventIngredient"] = field(default_factory=list)


@dataclass
class CookEventIngredient:
    id: int
    cook_event_id: int | None
    ingredient_id: int
    ingredient_name: str
    quantity: float
    unit: FoodUnit
    macros: IngredientMacros | None


@dataclass
class FoodNutritionGoals:
    id: int
    user_id: int
    kcal_target: int | None
    protein_g_target: float | None
    carbs_g_target: float | None
    fat_g_target: float | None
    updated_at: str


@dataclass
class GoalTarget:
    kcal_target: int | None = None
    protein_g_target: float | None = None
    carbs_g_target: float | None = None
    fat_g_target: float | None = None


@dataclass
class FoodOperationResult:
    ingredient: Ingredient | None = None
    stock: IngredientStock | None = None
    purchase: IngredientPurchase | None = None
    recipe: Recipe | None = None
    cook_event: CookEvent | None = None
    goals: FoodNutritionGoals | None = None
    status: FoodOperationStatus = FoodOperationStatus.OK


@dataclass
class SuggestResult:
    recipes: list[RecipeSummary]
    status: FoodOperationStatus = FoodOperationStatus.OK


@dataclass
class CookResult:
    cook_event: CookEvent | None
    macros: RecipeMacros | None
    status: FoodOperationStatus
    missing_ingredient_ids: list[int] = field(default_factory=list)
