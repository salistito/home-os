from modules.tasks.types import Task


class TaskAlreadyExistsError(Exception):
    """Raised when trying to create a task with an existing active name."""

    def __init__(self, task: Task):
        super().__init__(f"Task '{task.name}' already exists.")
        self.task = task
