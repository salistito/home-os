# users

Domain module for user management.

## Public API

```python
def create_user(user_name: str, role: str = "member") -> User

def get_users() -> list[User]

def get_active_users() -> list[User]

def get_user_by_name(user_name: str) -> User | None

def get_active_user_by_id(user_id: int) -> User | None

def get_active_user_by_name(user_name: str) -> User | None

def get_active_user_by_telegram_chat_id(telegram_chat_id: str) -> User | None

def update_user(user_id: int, **fields: str | int | None) -> bool

def delete_user(user_id: int) -> bool
```

Service layer:

```python
def register_user(user_name: str, role: str = "member", password: str | None = None, telegram_chat_id: str | None = None) -> User
```

## Key types

| Type | Description |
|---|---|
| `UserRole` | Enum: `ADMIN`, `MEMBER` |
| `User` | A household member with integer `id`, unique `name`, `role` (defaults to `member`), optional `password_hash`, optional `telegram_chat_id`, and optional `deleted_at` (soft-delete timestamp) |

## Errors

| Error | Description |
|---|---|
| `UserAlreadyExistsError` | Raised when creating a user with a duplicate name or telegram_chat_id |
| `UserNotFoundError` | Raised when a user is not found by id |

## Semantics

- `get_users()` returns **all** users, including soft-deleted ones. Use this for historical
  data display (ranking, board, finances entries).
- `get_active_users()` returns only users with `deleted_at IS NULL`. Use this for new
  operations (daily assignments, reminders, login).
- Individual lookups (`get_active_user_by_id`, `get_active_user_by_name`,
  `get_active_user_by_telegram_chat_id`) filter out
  soft-deleted users — they are meant for authentication and active operations.

## Dependencies

- `core/` for DB connection
- Does NOT import from `apps/`
