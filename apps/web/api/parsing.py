def parse_request_body(data: object) -> dict | None:
    if not isinstance(data, dict):
        return None
    return data


def parse_int_param(value: str | None) -> int | None | bool:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return False
