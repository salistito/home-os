from modules.reminders.types import Reminder


class ReminderAlreadyExistsError(Exception):
    def __init__(self, reminder: Reminder):
        super().__init__(f"Reminder '{reminder.message}' already exists.")
        self.reminder = reminder
