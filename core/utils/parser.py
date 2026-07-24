def float_or_none(value: object) -> float | None:
    if value is None:
        return None
    return float(value)
