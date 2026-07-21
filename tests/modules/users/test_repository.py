import pytest

import modules.users.repository as repository
from modules.users.errors import UserAlreadyExistsError


@pytest.mark.integration
def test_create_user_returns_user(db):
    user = repository.create_user("Alice")

    assert user.id is not None
    assert user.name == "Alice"
    assert user.role == "member"


@pytest.mark.integration
def test_create_duplicate_user_raises(db):
    repository.create_user("alice")

    with pytest.raises(UserAlreadyExistsError) as exc:
        repository.create_user("alice")
    assert exc.value.user.name == "Alice"


@pytest.mark.integration
def test_get_users_includes_db_user(db, db_user):
    users = repository.get_users()

    assert any(u.id == db_user.id for u in users)


@pytest.mark.integration
def test_get_active_users_excludes_deleted(db, db_user):
    repository.delete_user(db_user.id)
    users = repository.get_active_users()

    assert not any(u.id == db_user.id for u in users)


@pytest.mark.integration
def test_get_user_by_name_finds(db, db_user):
    user = repository.get_user_by_name("Test user")

    assert user is not None
    assert user.id == db_user.id


@pytest.mark.integration
def test_get_user_by_name_nonexistent(db):
    result = repository.get_user_by_name("nonexistent")

    assert result is None


@pytest.mark.integration
def test_get_active_user_by_id_finds(db, db_user):
    user = repository.get_active_user_by_id(db_user.id)

    assert user is not None
    assert user.id == db_user.id


@pytest.mark.integration
def test_get_active_user_by_id_nonexistent(db):
    result = repository.get_active_user_by_id(9999)

    assert result is None


@pytest.mark.integration
def test_get_active_user_by_name_normalized(db, db_user):
    user = repository.get_active_user_by_name("test user")

    assert user is not None
    assert user.id == db_user.id


@pytest.mark.integration
def test_get_active_user_by_telegram_chat_id_none(db, db_user):
    result = repository.get_active_user_by_telegram_chat_id("123456")

    assert result is None


@pytest.mark.integration
def test_update_user_name(db, db_user):
    result = repository.update_user(db_user.id, name="New Name")
    user = repository.get_active_user_by_id(db_user.id)

    assert result is True
    assert user.name == "New name"


@pytest.mark.integration
def test_update_user_password_hash(db, db_user):
    result = repository.update_user(db_user.id, password_hash="hash")
    user = repository.get_active_user_by_id(db_user.id)

    assert result is True
    assert user.password_hash == "hash"


@pytest.mark.integration
def test_update_user_telegram_chat_id(db, db_user):
    result = repository.update_user(db_user.id, telegram_chat_id="123")
    user = repository.get_active_user_by_id(db_user.id)

    assert result is True
    assert user.telegram_chat_id == "123"


@pytest.mark.integration
def test_update_user_no_fields(db, db_user):
    result = repository.update_user(db_user.id)

    assert result is True


@pytest.mark.integration
def test_update_user_invalid_field_raises(db, db_user):
    with pytest.raises(ValueError):
        repository.update_user(db_user.id, invalid_field="x")


@pytest.mark.integration
def test_delete_user_sets_deleted_at(db, db_user):
    result = repository.delete_user(db_user.id)
    user = repository.get_user_by_name("Test user")

    assert result is True
    assert user.deleted_at is not None


@pytest.mark.integration
def test_delete_user_nonexistent(db):
    result = repository.delete_user(9999)

    assert result is False


@pytest.mark.integration
def test_update_user_sets_column_to_null(db, db_user):
    result = repository.update_user(db_user.id, telegram_chat_id=None)
    user = repository.get_active_user_by_id(db_user.id)

    assert result is True
    assert user.telegram_chat_id is None


@pytest.mark.integration
def test_update_user_duplicate_name_raises_user_already_exists(db, db_user):
    alice = repository.create_user("Alice")

    with pytest.raises(UserAlreadyExistsError):
        repository.update_user(alice.id, name="Test User")
