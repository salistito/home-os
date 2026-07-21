import pytest

from core.utils.passwords import hash_password, verify_password


@pytest.mark.unit
class TestHashPassword:
    def test_returns_string(self):
        result = hash_password("secret")
        assert isinstance(result, str)

    def test_returns_bcrypt_hash(self):
        result = hash_password("secret")
        assert result.startswith("$2b$") or result.startswith("$2a$") or result.startswith("$2y$")

    def test_different_salts_produce_different_hashes(self):
        h1 = hash_password("secret")
        h2 = hash_password("secret")
        assert h1 != h2

    def test_long_password(self):
        result = hash_password("a" * 72)
        assert isinstance(result, str)

    def test_special_characters(self):
        result = hash_password("p@sswørd!🎉")
        assert isinstance(result, str)

    def test_empty_password(self):
        result = hash_password("")
        assert isinstance(result, str)

    def test_unicode_password(self):
        result = hash_password("contraseña")
        assert isinstance(result, str)


@pytest.mark.unit
class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        h = hash_password("secret")
        assert verify_password("secret", h) is True

    def test_wrong_password_returns_false(self):
        h = hash_password("secret")
        assert verify_password("wrong", h) is False

    def test_empty_hash_returns_false(self):
        assert verify_password("anything", "") is False

    def test_none_hash_returns_false(self):
        assert verify_password("anything", None) is False

    def test_whitespace_only_hash_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid salt"):
            verify_password("anything", "   ")

    def test_empty_password_empty_hash(self):
        assert verify_password("", "") is False

    def test_empty_password_valid_hash(self):
        h = hash_password("")
        assert verify_password("", h) is True

    def test_case_sensitive(self):
        h = hash_password("Secret")
        assert verify_password("secret", h) is False
        assert verify_password("Secret", h) is True

    def test_special_characters_match(self):
        h = hash_password("p@ss!")
        assert verify_password("p@ss!", h) is True
        assert verify_password("p@ss", h) is False

    def test_unicode_match(self):
        h = hash_password("contraseña")
        assert verify_password("contraseña", h) is True
        assert verify_password("contraseñe", h) is False

    def test_whitespace_difference(self):
        h = hash_password(" secret ")
        assert verify_password(" secret ", h) is True
        assert verify_password("secret", h) is False

    def test_short_hash_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid salt"):
            verify_password("secret", "abc")

    def test_random_string_hash_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid salt"):
            verify_password("secret", "not-a-bcrypt-hash")
