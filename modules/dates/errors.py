class CoupleAlreadyExistsError(Exception):
    def __init__(self, couple_id: int):
        super().__init__(f"Date couple {couple_id} already exists.")
        self.couple_id = couple_id


class EventAlreadyExistsError(Exception):
    def __init__(self, couple_id: int, week_start: str):
        super().__init__(f"Date event for couple {couple_id} on {week_start} already exists.")
        self.couple_id = couple_id
        self.week_start = week_start
