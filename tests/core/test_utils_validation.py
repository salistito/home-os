import pytest

from core.utils.validation import is_positive_number, is_valid_id


@pytest.mark.unit
@pytest.mark.parametrize("value", [1, 5, 0.5, 100])
def test_is_positive_number_valid(value):
    assert is_positive_number(value) is True


@pytest.mark.unit
@pytest.mark.parametrize("value", [0, -1, -0.5, True, False, "5", None, [1]])
def test_is_positive_number_invalid(value):
    assert is_positive_number(value) is False


@pytest.mark.unit
@pytest.mark.parametrize("value", [1, 42])
def test_is_valid_id_valid(value):
    assert is_valid_id(value) is True


@pytest.mark.unit
@pytest.mark.parametrize("value", [0, -1, True, 1.0, "3", None])
def test_is_valid_id_invalid(value):
    assert is_valid_id(value) is False
