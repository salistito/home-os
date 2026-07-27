from modules.food.types import Ingredient, Recipe


class IngredientAlreadyExistsError(Exception):
    def __init__(self, ingredient: Ingredient):
        super().__init__(f"Ingredient '{ingredient.name}' already exists.")
        self.ingredient = ingredient


class RecipeAlreadyExistsError(Exception):
    def __init__(self, recipe: Recipe):
        super().__init__(f"Recipe '{recipe.name}' already exists.")
        self.recipe = recipe


class InsufficientStockError(Exception):
    def __init__(self, ingredients: list[Ingredient]):
        ingredient_names = ", ".join(ingredient.name for ingredient in ingredients)
        super().__init__(f"Insufficient stock for: {ingredient_names}")
        self.ingredients = ingredients
