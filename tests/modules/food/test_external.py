from modules.food.external import parse_off_product


def test_parse_off_product_with_serving():
    product = {
        "product_name": "Arroz integral",
        "code": "123456",
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
    result = parse_off_product(product)
    assert result is not None
    name, external_id, macros = result
    assert name == "Arroz integral"
    assert external_id == "123456"
    assert macros["serving_amount"] == 100.0
    assert macros["serving_unit"] == "g"
    assert macros["kcal"] == 350


def test_parse_off_product_without_serving():
    product = {
        "product_name": "Leche",
        "code": "789",
        "serving_size": "250 ml",
        "nutriments": {
            "energy-kcal_100g": 60,
            "proteins_100g": 3.2,
            "carbohydrates_100g": 4.8,
            "fat_100g": 3.5,
            "fiber_100g": 0.0,
        },
    }
    result = parse_off_product(product)
    assert result is not None
    name, external_id, macros = result
    assert name == "Leche"
    assert external_id == "789"
    assert macros["serving_amount"] == 100.0
    assert macros["serving_unit"] == "ml"
    assert macros["kcal"] == 60


def test_parse_off_product_no_nutriments():
    product = {"product_name": "Test", "code": "123"}
    result = parse_off_product(product)
    assert result is None


def test_parse_off_product_no_name():
    product = {
        "product_name": "",
        "code": "123",
        "nutriments": {"energy-kcal_100g": 100},
    }
    result = parse_off_product(product)
    assert result is None


def test_parse_off_product_defaults():
    product = {
        "product_name": "Papa",
        "nutriments": {"energy-kcal_100g": 77},
    }
    result = parse_off_product(product)
    assert result is not None
    _, external_id, macros = result
    assert external_id == ""
    assert macros["serving_amount"] == 100.0
    assert macros["serving_unit"] == "g"
