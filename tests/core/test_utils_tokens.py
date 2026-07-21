import pytest
import jwt

from datetime import timedelta
from core.utils.date import get_now_utc
from core.utils.tokens import ALGORITHM, create_token, decode_token


@pytest.mark.unit
class TestCreateToken:
    def test_returns_string(self, jwt_secret, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", jwt_secret)
        token = create_token(1)
        assert isinstance(token, str)

    def test_token_has_three_parts(self, jwt_secret, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", jwt_secret)
        token = create_token(1)
        parts = token.split(".")
        assert len(parts) == 3

    def test_payload_contains_sub(self, jwt_secret, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", jwt_secret)
        token = create_token(1)
        payload = jwt.decode(token, jwt_secret, algorithms=[ALGORITHM])
        assert payload["sub"] == "1"

    def test_different_user_id_in_sub(self, jwt_secret, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", jwt_secret)
        token = create_token(42)
        payload = jwt.decode(token, jwt_secret, algorithms=[ALGORITHM])
        assert payload["sub"] == "42"

    def test_payload_has_iat(self, jwt_secret, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", jwt_secret)
        token = create_token(1)
        payload = jwt.decode(token, jwt_secret, algorithms=[ALGORITHM])
        assert "iat" in payload

    def test_payload_has_exp(self, jwt_secret, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", jwt_secret)
        token = create_token(1)
        payload = jwt.decode(token, jwt_secret, algorithms=[ALGORITHM])
        assert "exp" in payload

    def test_exp_is_future(self, jwt_secret, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", jwt_secret)
        token = create_token(1)
        payload = jwt.decode(token, jwt_secret, algorithms=[ALGORITHM])
        now = get_now_utc()
        assert payload["exp"] > now.timestamp()

    def test_zero_user_id(self, jwt_secret, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", jwt_secret)
        token = create_token(0)
        payload = jwt.decode(token, jwt_secret, algorithms=[ALGORITHM])
        assert payload["sub"] == "0"

    def test_large_user_id(self, jwt_secret, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", jwt_secret)
        token = create_token(999999)
        payload = jwt.decode(token, jwt_secret, algorithms=[ALGORITHM])
        assert payload["sub"] == "999999"

    def test_negative_user_id(self, jwt_secret, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", jwt_secret)
        token = create_token(-1)
        payload = jwt.decode(token, jwt_secret, algorithms=[ALGORITHM])
        assert payload["sub"] == "-1"

    def test_empty_secret_raises_runtime_error(self, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", "")
        with pytest.raises(RuntimeError, match="JWT_SECRET"):
            create_token(1)

    def test_different_keys_produce_different_tokens(self, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", "this-is-a-long-enough-test-key-a-ok")
        token_a = create_token(1)
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", "this-is-a-long-enough-test-key-b-ok")
        token_b = create_token(1)
        assert token_a != token_b

    def test_tokens_are_valid_jwt_format(self, jwt_secret, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", jwt_secret)
        token = create_token(1)
        parts = token.split(".")
        assert len(parts) == 3
        for part in parts:
            assert len(part) > 0


@pytest.mark.unit
class TestDecodeToken:
    def test_decodes_valid_token(self, jwt_secret, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", jwt_secret)
        token = create_token(1)
        result = decode_token(token)
        assert result == 1

    def test_decodes_different_user_id(self, jwt_secret, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", jwt_secret)
        token = create_token(42)
        result = decode_token(token)
        assert result == 42

    def test_invalid_token_returns_none(self, jwt_secret, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", jwt_secret)
        result = decode_token("invalid.token.here")
        assert result is None

    def test_empty_token_returns_none(self, jwt_secret, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", jwt_secret)
        result = decode_token("")
        assert result is None

    def test_token_signed_with_different_key(self, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", "this-is-a-long-enough-test-key-a-ok")
        token = create_token(1)
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", "this-is-a-long-enough-test-key-b-ok")
        result = decode_token(token)
        assert result is None

    def test_expired_token(self, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", "a-long-enough-test-key-for-tokens-32b")
        now = get_now_utc()
        expired_payload = {
            "sub": "1",
            "iat": now - timedelta(days=30),
            "exp": now - timedelta(days=1),
        }
        token = jwt.encode(expired_payload, "a-long-enough-test-key-for-tokens-32b", algorithm=ALGORITHM)
        result = decode_token(token)
        assert result is None

    def test_token_without_sub(self, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", "a-long-enough-test-key-for-tokens-32b")
        now = get_now_utc()
        payload = {"iat": now, "exp": now + timedelta(days=1)}
        token = jwt.encode(payload, "a-long-enough-test-key-for-tokens-32b", algorithm=ALGORITHM)
        result = decode_token(token)
        assert result is None

    def test_token_with_non_numeric_sub(self, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", "a-long-enough-test-key-for-tokens-32b")
        now = get_now_utc()
        payload = {
            "sub": "not_a_number",
            "iat": now,
            "exp": now + timedelta(days=1),
        }
        token = jwt.encode(payload, "a-long-enough-test-key-for-tokens-32b", algorithm=ALGORITHM)
        result = decode_token(token)
        assert result is None

    def test_token_with_none_sub(self, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", "a-long-enough-test-key-for-tokens-32b")
        now = get_now_utc()
        payload = {"sub": None, "iat": now, "exp": now + timedelta(days=1)}
        token = jwt.encode(payload, "a-long-enough-test-key-for-tokens-32b", algorithm=ALGORITHM)
        result = decode_token(token)
        assert result is None

    def test_tampered_token(self, jwt_secret, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", jwt_secret)
        token = create_token(1)
        parts = token.split(".")
        tampered = parts[0] + "." + parts[1] + "." + "A" * len(parts[2])
        result = decode_token(tampered)
        assert result is None

    def test_zero_user_id_token(self, jwt_secret, monkeypatch):
        monkeypatch.setattr("core.utils.tokens.JWT_SECRET", jwt_secret)
        token = create_token(0)
        result = decode_token(token)
        assert result == 0
