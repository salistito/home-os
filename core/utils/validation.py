def is_valid_id(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def is_positive_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0
