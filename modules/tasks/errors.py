from modules.tasks.types import Task


class TaskAlreadyExistsError(Exception):
    def __init__(self, task: Task):
        super().__init__(f"Task '{task.name}' already exists.")
        self.task = task


class TaskNotFoundError(Exception):
    def __init__(self, task_id: int):
        super().__init__(f"Task with id={task_id} not found.")
        self.task_id = task_id
