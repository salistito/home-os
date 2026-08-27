from modules.fitness.types import Exercise, Routine, WeightEntry


class ExerciseAlreadyExistsError(Exception):
    def __init__(self, exercise: Exercise):
        super().__init__(f"Exercise '{exercise.name}' already exists.")
        self.exercise = exercise


class RoutineAlreadyExistsError(Exception):
    def __init__(self, routine: Routine):
        super().__init__(f"Routine '{routine.name}' already exists.")
        self.routine = routine


class WeightEntryDateConflictError(Exception):
    def __init__(self, weight_entry: WeightEntry):
        super().__init__(f"A weight entry for {weight_entry.measured_at} already exists.")
        self.weight_entry = weight_entry
