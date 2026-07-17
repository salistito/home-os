# users

Domain module for user management.

## Public API

```python
def get_users() -> list[User]

def get_user_by_id(user_id: str) -> User | None

def get_user_by_chat_id(chat_id: str) -> User | None

def get_password_hash(user_id: str) -> str | None
```

## Key types

| Type | Description |
|---|---|
| `User` | A household member with `id`, `name`, `telegram_chat_id`, and optional `password_hash` |

## Dependencies

- `core/` for DB connection
- Does NOT import from `apps/`
