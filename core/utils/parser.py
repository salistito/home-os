def float_or_none(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def normalize_optional_text(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
