from modules.tasks.types import Assignment, MarkTaskResult, MarkTaskStatus


def format_mark_done(result: MarkTaskResult) -> str:
    if result.status == MarkTaskStatus.OK:
        return f"Listo: {result.task_name} (+{result.points_awarded} pts)"
    return "No encontré esa tarea para hoy."


def format_balance(month: str, balance: dict[str, int], names: dict[str, str]) -> str:
    lines = [f"Balance {month}:"]
    for user_id, points in sorted(balance.items()):
        label = names.get(user_id, user_id)
        lines.append(f"• {label}: {points} pts")
    return "\n".join(lines)


def format_morning_message(name: str, tasks: list[Assignment], completed_ids: set[int] | None = None) -> str:
    if completed_ids is None:
        completed_ids = set()
    
    lines = [f"Buenos días, {name}!", "", "Hoy te toca:"]
    for task in tasks:
        emoji = "✅" if task.task_id in completed_ids else "⭕"
        lines.append(f"{emoji} {task.task_name} ({task.points} pts)")
    return "\n".join(lines)
