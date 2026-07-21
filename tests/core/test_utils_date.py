import pytest

from datetime import date, datetime, timezone

import core.utils.date as date_utils


@pytest.mark.unit
class TestGetNow:
    def test_returns_datetime_with_tz(self, frozen_now):
        result = date_utils.get_now()
        assert result == frozen_now
        assert result.tzinfo is not None

    def test_returns_frozen_value(self, frozen_now):
        result = date_utils.get_now()
        assert result.year == 2026
        assert result.month == 3
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30


@pytest.mark.unit
def test_real_get_now_returns_datetime_with_tz():
    result = date_utils.get_now()
    assert isinstance(result, datetime)
    assert result.tzinfo is not None


@pytest.mark.unit
class TestGetToday:
    def test_returns_date(self, frozen_today):
        result = date_utils.get_today()
        assert result == frozen_today
        assert isinstance(result, date)
        assert not isinstance(result, datetime)

    def test_returns_frozen_value(self, frozen_today):
        result = date_utils.get_today()
        assert result.year == 2026
        assert result.month == 3
        assert result.day == 15


@pytest.mark.unit
class TestGetNowUtc:
    def test_returns_utc_datetime(self, frozen_now_utc):
        result = date_utils.get_now_utc()
        assert result == frozen_now_utc
        assert result.tzinfo == timezone.utc

    def test_returns_frozen_value(self, frozen_now_utc):
        result = date_utils.get_now_utc()
        assert result.year == 2026
        assert result.month == 3
        assert result.day == 15
        assert result.hour == 14
        assert result.minute == 30


@pytest.mark.unit
class TestFormatDate:
    def test_standard_date(self):
        assert date_utils.format_date("2026-03-15") == "15/03/2026"

    def test_start_of_year(self):
        assert date_utils.format_date("2026-01-01") == "01/01/2026"

    def test_end_of_year(self):
        assert date_utils.format_date("2026-12-31") == "31/12/2026"

    def test_leap_day(self):
        assert date_utils.format_date("2024-02-29") == "29/02/2024"

    def test_single_digit_day(self):
        assert date_utils.format_date("2026-03-05") == "05/03/2026"

    def test_single_digit_month(self):
        assert date_utils.format_date("2026-01-15") == "15/01/2026"


@pytest.mark.unit
class TestFormatDateShort:
    def test_monday(self):
        assert date_utils.format_date_short("2026-03-16") == "lun 16"

    def test_tuesday(self):
        assert date_utils.format_date_short("2026-03-17") == "mar 17"

    def test_wednesday(self):
        assert date_utils.format_date_short("2026-03-18") == "mié 18"

    def test_thursday(self):
        assert date_utils.format_date_short("2026-03-19") == "jue 19"

    def test_friday(self):
        assert date_utils.format_date_short("2026-03-20") == "vie 20"

    def test_saturday(self):
        assert date_utils.format_date_short("2026-03-21") == "sáb 21"

    def test_sunday(self):
        assert date_utils.format_date_short("2026-03-15") == "dom 15"

    def test_single_digit_day_padded(self):
        assert date_utils.format_date_short("2026-03-01") == "dom 01"

    def test_double_digit_day(self):
        assert date_utils.format_date_short("2026-03-25") == "mié 25"


@pytest.mark.unit
class TestToDbDate:
    def test_standard_date(self):
        assert date_utils.to_db_date(date(2026, 3, 15)) == "2026-03-15"

    def test_start_of_year(self):
        assert date_utils.to_db_date(date(2026, 1, 1)) == "2026-01-01"

    def test_end_of_year(self):
        assert date_utils.to_db_date(date(2026, 12, 31)) == "2026-12-31"

    def test_leap_day(self):
        assert date_utils.to_db_date(date(2024, 2, 29)) == "2024-02-29"


@pytest.mark.unit
class TestIsIsoformatDate:
    def test_valid_date(self):
        assert date_utils.is_isoformat_date("2026-03-15") is True

    def test_start_of_year(self):
        assert date_utils.is_isoformat_date("2026-01-01") is True

    def test_end_of_year(self):
        assert date_utils.is_isoformat_date("2026-12-31") is True

    def test_leap_day_valid(self):
        assert date_utils.is_isoformat_date("2024-02-29") is True

    def test_invalid_date_feb_30(self):
        assert date_utils.is_isoformat_date("2026-02-30") is False

    def test_invalid_date_month_13(self):
        assert date_utils.is_isoformat_date("2026-13-01") is False

    def test_invalid_date_month_0(self):
        assert date_utils.is_isoformat_date("2026-00-01") is False

    def test_invalid_date_day_0(self):
        assert date_utils.is_isoformat_date("2026-01-00") is False

    def test_invalid_date_day_32(self):
        assert date_utils.is_isoformat_date("2026-01-32") is False

    def test_invalid_date_april_31(self):
        assert date_utils.is_isoformat_date("2026-04-31") is False

    def test_non_leap_year_feb_29(self):
        assert date_utils.is_isoformat_date("2025-02-29") is False

    def test_empty_string(self):
        assert date_utils.is_isoformat_date("") is False

    def test_plain_text(self):
        assert date_utils.is_isoformat_date("not a date") is False

    def test_wrong_format_slashes(self):
        assert date_utils.is_isoformat_date("2026/03/15") is False

    def test_wrong_format_no_leading_zeros(self):
        assert date_utils.is_isoformat_date("2026-3-15") is False

    def test_wrong_format_extra_chars(self):
        assert date_utils.is_isoformat_date("2026-03-15T00:00:00") is False

    def test_wrong_format_too_short(self):
        assert date_utils.is_isoformat_date("2026-03") is False

    def test_wrong_format_us_style(self):
        assert date_utils.is_isoformat_date("03-15-2026") is False

    def test_only_numbers(self):
        assert date_utils.is_isoformat_date("20260315") is False

    def test_none_value(self):
        with pytest.raises(TypeError):
            date_utils.is_isoformat_date(None)


@pytest.mark.unit
class TestNextDueDate:
    def test_seven_days(self):
        assert date_utils.next_due_date(date(2026, 3, 15), 7) == "2026-03-22"

    def test_one_day(self):
        assert date_utils.next_due_date(date(2026, 3, 15), 1) == "2026-03-16"

    def test_zero_days(self):
        assert date_utils.next_due_date(date(2026, 3, 15), 0) == "2026-03-15"

    def test_thirty_days(self):
        assert date_utils.next_due_date(date(2026, 3, 15), 30) == "2026-04-14"

    def test_cross_month_boundary(self):
        assert date_utils.next_due_date(date(2026, 3, 31), 1) == "2026-04-01"

    def test_cross_year_boundary(self):
        assert date_utils.next_due_date(date(2026, 12, 31), 1) == "2027-01-01"

    def test_leap_year_transition(self):
        assert date_utils.next_due_date(date(2024, 2, 28), 1) == "2024-02-29"

    def test_large_frequency(self):
        assert date_utils.next_due_date(date(2026, 1, 1), 365) == "2027-01-01"


@pytest.mark.unit
class TestMonthKey:
    def test_march(self):
        assert date_utils.month_key(date(2026, 3, 15)) == "2026-03"

    def test_january(self):
        assert date_utils.month_key(date(2026, 1, 1)) == "2026-01"

    def test_december(self):
        assert date_utils.month_key(date(2026, 12, 31)) == "2026-12"

    def test_october(self):
        assert date_utils.month_key(date(2026, 10, 5)) == "2026-10"

    def test_different_year(self):
        assert date_utils.month_key(date(2025, 6, 15)) == "2025-06"
