from core.utils.passwords import hash_password
from modules.users import repository
from modules.users.errors import UserAlreadyExistsError
from modules.users.types import User, UserRole


def create_user(
    user_name: str,
    role: str = UserRole.MEMBER,
    password: str | None = None,
    telegram_chat_id: str | None = None,
) -> User:
    existing_by_name = repository.get_active_user_by_name(user_name)
    if existing_by_name is not None:
        raise UserAlreadyExistsError(existing_by_name)

    if telegram_chat_id is not None:
        existing = repository.get_active_user_by_telegram_chat_id(telegram_chat_id)
        if existing is not None:
            raise UserAlreadyExistsError(existing)

    user = repository.create_user(user_name, role=role)

    fields = {}
    if password is not None:
        fields["password_hash"] = hash_password(password)
    if telegram_chat_id is not None:
        fields["telegram_chat_id"] = telegram_chat_id
    if fields:
        repository.update_user(user.id, **fields)
        return repository.get_active_user_by_id(user.id)
    return user
