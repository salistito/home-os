import random

from modules.tasks.types import Task
from modules.users.types import User

BRUTE_FORCE_LIMIT = 1_000_000


def find_greedy_assignment(
    users: list[User],
    tasks: list[Task],
    current_points: dict[int, int],
) -> list[int]:
    """
    Greedy load-balancing strategy.

    Tasks are processed from largest to smallest.
    Each task is assigned to a user with the lowest
    current projected score.

    If multiple users have the same score,
    one is selected randomly.
    """

    assignee_ids = []
    projected_points = current_points.copy()

    for task in tasks:
        min_projected_points = min(projected_points[user.id] for user in users)
        candidates = [user for user in users if projected_points[user.id] == min_projected_points]
        assignee = random.choice(candidates)

        projected_points[assignee.id] += task.points
        assignee_ids.append(assignee.id)

    return assignee_ids


def _calculate_fairness_score(
    projected_points: dict[int, int],
    disadvantaged_user_id: int,
) -> tuple[int, int]:
    """
    Return the fairness score.

    Lower is better.

    Priority:
        1. Smaller sum of squared points (equivalently,
           smaller deviation from an equal split).
           This actively reduces any existing historical gap
           by pulling points toward the fair share.
        2. Higher score for the disadvantaged user.
    """

    point_values = list(projected_points.values())

    sum_of_squares = sum(points**2 for points in point_values)

    disadvantaged_user_points = projected_points[disadvantaged_user_id]

    return (
        sum_of_squares,
        -disadvantaged_user_points,
    )


def _calculate_lower_bound_sum_of_squares(
    projected_points: dict[int, int],
    remaining_points: int,
) -> float:
    """
    Calculate an optimistic lower bound for the minimum
    possible sum of squares.

    The relaxation allows the remaining task points to be
    split arbitrarily between users.

    This is more optimistic than the real problem, where
    tasks are indivisible, so it is safe for Branch & Bound.
    """

    point_values = sorted(projected_points.values())
    number_of_users = len(point_values)

    if number_of_users == 0:
        return 0.0

    remaining = remaining_points
    lower_bound = 0.0

    for index in range(number_of_users - 1):
        current_level = point_values[index]
        next_level = point_values[index + 1]

        users_at_current_level = index + 1

        points_needed = (next_level - current_level) * users_at_current_level

        if remaining < points_needed:
            # We cannot reach the next level.
            # Spread the remaining points evenly among
            # the users currently at the lowest level.
            final_level = current_level + remaining / users_at_current_level

            lower_bound += users_at_current_level * final_level**2

            lower_bound += sum(points**2 for points in point_values[index + 1 :])

            return lower_bound

        # Raise all users currently at the lower level
        # to the next level.
        lower_bound += users_at_current_level * next_level**2

        remaining -= points_needed

    # All users are now at the same level.
    final_level = point_values[-1] + remaining / number_of_users

    lower_bound = number_of_users * final_level**2

    return lower_bound


def find_optimal_assignment(
    users: list[User],
    tasks: list[Task],
    current_points: dict[int, int],
) -> list[int]:
    """
    Find the optimal assignment using Branch & Bound.

    Fairness criteria, in priority order:

    1. Minimize the sum of squared final points:
           sum(points^2)

       Since the total number of points is fixed,
       this is equivalent to minimizing the deviation
       from an equal split. It actively pulls points
       toward the fair share, reducing any historical gap.

    2. If tied, maximize the final score of the
       user who started with the lowest score
       (to help the losing user catch up).
    """

    if not users or not tasks:
        return []

    user_ids = [user.id for user in users]
    task_points = [task.points for task in tasks]

    # If several users start with the same lowest score,
    # randomly select which one gets the fairness bonus.
    min_initial_points = min(current_points[user_id] for user_id in user_ids)
    lowest_score_users = [
        user_id for user_id in user_ids if current_points[user_id] == min_initial_points
    ]
    disadvantaged_user_id = random.choice(lowest_score_users)

    # ---------------------------------------------------------
    # Get an initial feasible solution.
    # This gives Branch & Bound a good upper bound immediately.
    # ---------------------------------------------------------
    greedy_assignment = find_greedy_assignment(users, tasks, current_points)
    best_projected_points = current_points.copy()

    for task, user_id in zip(tasks, greedy_assignment):
        best_projected_points[user_id] += task.points

    best_assignment = greedy_assignment.copy()
    best_score = _calculate_fairness_score(best_projected_points, disadvantaged_user_id)

    # ---------------------------------------------------------
    # Search state.
    # ---------------------------------------------------------
    projected_points = current_points.copy()
    current_assignment = [None] * len(tasks)

    # remaining_task_points[i] contains the total weight of tasks from i onward.
    remaining_task_points = [0] * (len(tasks) + 1)

    for task_index in range(len(tasks) - 1, -1, -1):
        remaining_task_points[task_index] = (
            remaining_task_points[task_index + 1] + task_points[task_index]
        )

    def search(
        task_index: int,
        current_sum_of_squares: int,
    ) -> None:
        nonlocal best_score
        nonlocal best_projected_points
        nonlocal best_assignment

        # All tasks have been assigned.
        if task_index == len(tasks):
            candidate_score = _calculate_fairness_score(
                projected_points=projected_points,
                disadvantaged_user_id=disadvantaged_user_id,
            )

            if candidate_score < best_score:
                best_score = candidate_score
                best_projected_points = projected_points.copy()
                best_assignment = current_assignment.copy()

            return

        remaining_points = remaining_task_points[task_index]

        # -----------------------------------------------------
        # Branch & Bound pruning.
        #
        # We calculate an optimistic lower bound for the
        # sum of squares. If even that optimistic solution
        # cannot beat the current solution, stop exploring.
        # -----------------------------------------------------

        lower_bound = _calculate_lower_bound_sum_of_squares(
            projected_points=projected_points,
            remaining_points=remaining_points,
        )

        current_best_sum_of_squares = best_score[0]

        if lower_bound > current_best_sum_of_squares:
            return

        task = tasks[task_index]

        # Explore users with lower current scores first.
        candidate_user_ids = sorted(
            user_ids,
            key=lambda user_id: projected_points[user_id],
        )

        # If two users have exactly the same score, they are
        # normally symmetric. We only need to explore one of
        # them, except for the disadvantaged user because the
        # third fairness criterion distinguishes that user.
        seen_points = set()

        for user_id in candidate_user_ids:
            user_points = projected_points[user_id]

            if user_id != disadvantaged_user_id and user_points in seen_points:
                continue

            if user_id != disadvantaged_user_id:
                seen_points.add(user_points)

            # Assign task.
            projected_points[user_id] += task.points
            current_assignment[task_index] = user_id

            new_sum_of_squares = (
                current_sum_of_squares - user_points**2 + projected_points[user_id] ** 2
            )

            search(
                task_index=task_index + 1,
                current_sum_of_squares=new_sum_of_squares,
            )

            # Backtrack.
            projected_points[user_id] = user_points
            current_assignment[task_index] = None

    initial_sum_of_squares = sum(points**2 for points in projected_points.values())

    search(
        task_index=0,
        current_sum_of_squares=initial_sum_of_squares,
    )

    return best_assignment
