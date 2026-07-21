import pytest

from unittest.mock import patch

from modules.users.errors import UserAlreadyExistsError
from modules.users.service import register_user


@pytest.mark.unit
@patch("modules.users.service.hash_password")
@patch("modules.users.service.repository")
def test_register_user_creates_via_repository(mock_repo, mock_hash, db_user):
    mock_repo.get_active_user_by_name.return_value = None
    mock_repo.get_active_user_by_telegram_chat_id.return_value = None
    mock_repo.create_user.return_value = db_user

    result = register_user("NewUser")

    mock_repo.create_user.assert_called_once_with("NewUser", role="member")
    assert result == db_user


@pytest.mark.unit
@patch("modules.users.service.repository")
def test_register_user_already_exists_by_name(mock_repo, db_user):
    mock_repo.get_active_user_by_name.return_value = db_user

    with pytest.raises(UserAlreadyExistsError) as exc:
        register_user("Test User")
    assert exc.value.user == db_user


@pytest.mark.unit
@patch("modules.users.service.repository")
def test_register_user_telegram_chat_id_taken(mock_repo, db_user):
    mock_repo.get_active_user_by_name.return_value = None
    mock_repo.get_active_user_by_telegram_chat_id.return_value = db_user

    with pytest.raises(UserAlreadyExistsError) as exc:
        register_user("NewUser", telegram_chat_id="123")
    assert exc.value.user == db_user


@pytest.mark.unit
@patch("modules.users.service.hash_password", return_value="hashed")
@patch("modules.users.service.repository")
def test_register_user_with_password_calls_hash_and_update(mock_repo, mock_hash, db_user):
    mock_repo.get_active_user_by_name.return_value = None
    mock_repo.get_active_user_by_telegram_chat_id.return_value = None
    mock_repo.create_user.return_value = db_user
    mock_repo.get_active_user_by_id.return_value = db_user

    result = register_user("NewUser", password="secret")

    mock_hash.assert_called_once_with("secret")
    mock_repo.update_user.assert_called_once_with(db_user.id, password_hash="hashed")
    mock_repo.get_active_user_by_id.assert_called_once_with(db_user.id)
    assert result == db_user


@pytest.mark.unit
@patch("modules.users.service.repository")
def test_register_user_with_telegram_chat_id_calls_update(mock_repo, db_user):
    mock_repo.get_active_user_by_name.return_value = None
    mock_repo.get_active_user_by_telegram_chat_id.return_value = None
    mock_repo.create_user.return_value = db_user
    mock_repo.get_active_user_by_id.return_value = db_user

    result = register_user("NewUser", telegram_chat_id="123")

    mock_repo.update_user.assert_called_once_with(db_user.id, telegram_chat_id="123")
    assert result == db_user


@pytest.mark.unit
@patch("modules.users.service.repository")
def test_register_user_no_password_or_telegram_returns_directly(mock_repo, db_user):
    mock_repo.get_active_user_by_name.return_value = None
    mock_repo.get_active_user_by_telegram_chat_id.return_value = None
    mock_repo.create_user.return_value = db_user

    result = register_user("NewUser")

    mock_repo.update_user.assert_not_called()
    assert result == db_user
