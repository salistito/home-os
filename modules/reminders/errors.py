from modules.reminders.types import Reminder


class ReminderAlreadyExistsError(Exception):
    def __init__(self, reminder: Reminder):
        super().__init__(f"Reminder '{reminder.message}' already exists.")
        self.reminder = reminder


class ReminderNotFoundError(Exception):
    def __init__(self, reminder_id: int):
        super().__init__(f"Reminder with id={reminder_id} not found.")
        self.reminder_id = reminder_id
