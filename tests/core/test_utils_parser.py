import pytest

from core.utils.parser import float_or_none, normalize_optional_text


@pytest.mark.unit
@pytest.mark.parametrize(
    "value, expected",
    [
        (None, None),
        ("3.5", 3.5),
        (2, 2.0),
        (1.5, 1.5),
    ],
)
def test_float_or_none(value, expected):
    assert float_or_none(value) == expected


@pytest.mark.unit
def test_float_or_none_invalid_raises():
    with pytest.raises(ValueError):
        float_or_none("nope")


@pytest.mark.unit
@pytest.mark.parametrize(
    "value, expected",
    [
        (None, None),
        ("", None),
        ("   ", None),
        ("  hola  ", "hola"),
        ("x", "x"),
        (42, "42"),
    ],
)
def test_normalize_optional_text(value, expected):
    assert normalize_optional_text(value) == expected
