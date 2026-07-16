from modules.finances.types import Period


class OpenPeriodExistsError(Exception):
    def __init__(self, period: Period):
        super().__init__(f"An open period already exists: '{period.label}'.")
        self.period = period
