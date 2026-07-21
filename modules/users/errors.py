from modules.users.types import User


class UserAlreadyExistsError(Exception):
    def __init__(self, user: User):
        super().__init__(f"User '{user.name}' already exists.")
        self.user = user