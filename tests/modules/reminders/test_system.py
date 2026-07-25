import pytest

from modules.reminders.system import SystemRef, module_icon


class TestSystemRef:
    @pytest.mark.unit
    def test_parse_valid(self):
        ref = SystemRef.parse("food:low_stock")
        assert ref.module == "food"
        assert ref.detail == "low_stock"

    @pytest.mark.unit
    def test_parse_with_colon_in_detail(self):
        ref = SystemRef.parse("food:stock:low")
        assert ref.module == "food"
        assert ref.detail == "stock:low"

    @pytest.mark.unit
    def test_parse_no_colon_raises(self):
        with pytest.raises(ValueError):
            SystemRef.parse("invalid")

    @pytest.mark.unit
    def test_parse_empty_module_raises(self):
        with pytest.raises(ValueError):
            SystemRef.parse(":detail")

    @pytest.mark.unit
    def test_parse_empty_detail_raises(self):
        with pytest.raises(ValueError):
            SystemRef.parse("module:")

    @pytest.mark.unit
    def test_str(self):
        ref = SystemRef("food", "low_stock")
        assert str(ref) == "food:low_stock"

    @pytest.mark.unit
    def test_frozen(self):
        ref = SystemRef("food", "low_stock")
        with pytest.raises(AttributeError):
            ref.module = "tasks"


class TestModuleIcon:
    @pytest.mark.unit
    def test_known_module_food(self):
        ref = SystemRef("food", "low_stock")
        assert module_icon(ref) == "🍱"

    @pytest.mark.unit
    def test_known_module_tasks(self):
        ref = SystemRef("tasks", "overdue")
        assert module_icon(ref) == "📋"

    @pytest.mark.unit
    def test_known_module_finances(self):
        ref = SystemRef("finances", "high_expense")
        assert module_icon(ref) == "💰"

    @pytest.mark.unit
    def test_unknown_module(self):
        ref = SystemRef("unknown", "action")
        assert module_icon(ref) == ""

    @pytest.mark.unit
    def test_none_returns_empty(self):
        assert module_icon(None) == ""
