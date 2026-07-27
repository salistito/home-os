from modules.food.suggest import (
    nutrition_closeness,
    variety_score,
)
from modules.food.types import GoalTarget

# -- Nutrition closeness scoring --


def test_nutrition_closeness_exact_match():
    target = GoalTarget(kcal_target=250, protein_g_target=26)
    per_portion = {"kcal": 250.0, "protein_g": 26.0, "carbs_g": 0.0, "fat_g": 15.0, "fiber_g": 0.0}
    score = nutrition_closeness(per_portion, target)
    assert score == 1.0


def test_nutrition_closeness_partial_match():
    target = GoalTarget(kcal_target=250, protein_g_target=26)
    per_portion = {"kcal": 200.0, "protein_g": 26.0, "carbs_g": 0.0, "fat_g": 0.0, "fiber_g": 0.0}
    score = nutrition_closeness(per_portion, target)
    assert 0.0 < score < 1.0


def test_nutrition_closeness_no_targets():
    target = GoalTarget()
    per_portion = {"kcal": 250.0, "protein_g": 26.0, "carbs_g": 0.0, "fat_g": 15.0, "fiber_g": 0.0}
    score = nutrition_closeness(per_portion, target)
    assert score == 1.0


def test_nutrition_closeness_zero_target():
    target = GoalTarget(kcal_target=0)
    per_portion = {"kcal": 250.0, "protein_g": 26.0, "carbs_g": 0.0, "fat_g": 15.0, "fiber_g": 0.0}
    score = nutrition_closeness(per_portion, target)
    assert score == 1.0


# -- Variety scoring --


def test_variety_score_no_history():
    score = variety_score(1, [])
    assert score == 1.0


def test_variety_score_never_cooked():
    score = variety_score(99, [1, 2, 3])
    assert score == 1.0


def test_variety_score_recently_cooked():
    score = variety_score(1, [1, 2, 3])
    assert score < 1.0


def test_variety_score_oldest_in_history():
    score = variety_score(3, [1, 2, 3])
    assert score > 0.5
