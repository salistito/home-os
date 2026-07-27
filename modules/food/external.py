import requests

# Open Food Facts Search API: https://wiki.openfoodfacts.org/Open_Food_Facts_Search_API_Version_2
# No authentication required.
# Rate limit: be polite, max ~10 req/s. We use a 10 s timeout per request.

OPEN_FOOD_FACTS_URL = "https://world.openfoodfacts.org/cgi/search.pl"


def search_open_food_facts(name: str) -> list[dict]:
    """
    Search Open Food Facts for products matching *name*.

    Returns a list of raw product dicts (up to 5 results).
    Each dict contains keys: code, product_name, brands, nutriments,
    serving_size, serving_quantity.

    Raises requests.HTTPError on non-2xx responses.
    """
    resp = requests.get(
        OPEN_FOOD_FACTS_URL,
        params={
            "search_terms": name,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": 5,
            "fields": "code,product_name,brands,nutriments,serving_size,serving_quantity",
        },
        headers={"User-Agent": "HomeOS/1.0"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("products", [])


def parse_off_product(product: dict) -> tuple[str, str, dict] | None:
    """
    Extract a normalized macro dict from an Open Food Facts product.

    Returns (product_name, external_id, macros_dict) on success,
    or None if the product lacks nutriments or a name.

    Macro keys: serving_amount, serving_unit, kcal, protein_g, carbs_g,
    fat_g, fiber_g. Uses _serving values when available, falls back to
    _100g. serving_unit is "ml" if serving_size contains "ml", else "g".
    """
    nutriments = product.get("nutriments")
    if not nutriments:
        return None

    product_name = product.get("product_name", "").strip()
    if not product_name:
        return None

    serving_qty_str = product.get("serving_quantity")
    serving_size_str = product.get("serving_size", "")
    if serving_qty_str is not None:
        try:
            serving_amount = float(serving_qty_str)
        except (TypeError, ValueError):
            serving_amount = 100.0
    else:
        serving_amount = 100.0

    if serving_size_str and "ml" in serving_size_str.lower():
        serving_unit = "ml"
    else:
        serving_unit = "g"

    has_serving = serving_qty_str is not None and serving_amount > 0
    suffix = "_serving" if has_serving else "_100g"

    macros: dict = {
        "serving_amount": serving_amount,
        "serving_unit": serving_unit,
        "kcal": nutriments.get(f"energy-kcal{suffix}"),
        "protein_g": nutriments.get(f"proteins{suffix}"),
        "carbs_g": nutriments.get(f"carbohydrates{suffix}"),
        "fat_g": nutriments.get(f"fat{suffix}"),
        "fiber_g": nutriments.get(f"fiber{suffix}"),
    }

    external_id = product.get("code", "")
    return product_name, external_id, macros
