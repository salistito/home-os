from modules.users.types import User


class UserAlreadyExistsError(Exception):
    def __init__(self, user: User):
        super().__init__(f"User '{user.name}' already exists.")
        self.user = user


class UserNotFoundError(Exception):
    def __init__(self, user_id: int):
        super().__init__(f"User with id={user_id} not found.")
        self.user_id = user_id