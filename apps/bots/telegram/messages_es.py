from modules.tasks.types import Assignment


def start_welcome() -> str:
    return (
        "👋 ¡Hola! Bienvenido/a a HomeOS:\nEl sistema para organizar tu hogar. 🏠\n\n"
        "🎯 Aquí podrás gestionar tus tareas diarias y sumar puntos por cumplirlas. 🏆\n\n"
        "📋 Usa /tasks para ver tus tareas asignadas para el día.\n"
        "📝 Presiona el botón de una tarea o envía su nombre para marcarla como realizada.\n"
        "📊 Usa /balance para ver tus puntos acumulados durante el mes.\n\n"
        "💡 Puedes volver a ver este mensaje ejecutando el comando /start o /help.\n\n"
        "¡Mucha suerte! 💪"
    )


def user_not_registered() -> str:
    return "❌ No estás registrado. Pídele a un administrador que registre tu chat_id en la aplicación."


def task_not_found(searched_text: str | None) -> str:
    if not searched_text:
        return "❌ No encontré esa tarea"
    return f"❌ No encontré la tarea '{searched_text}'"


def task_already_done(task_name: str) -> str:
    return f"ℹ️ Hoy ya se completó la tarea '{task_name}'"


def tasks_updated() -> str:
    return "✨ Tareas actualizadas correctamente"


def no_pending_tasks() -> str:
    return "🎉 No tienes tareas pendientes para hoy. ¡Disfruta el día! 😊"


def no_tasks_today(user_name: str) -> str:
    return f"🌅 ¡Buenos días, {user_name}!\n\n{no_pending_tasks()}"


def morning_message(
    user_name: str, tasks: list[Assignment], completed_ids: set[int] | None = None
) -> str:
    return f"🌅 ¡Buenos días, {user_name}!\n\n{tasks_list(tasks, completed_ids)}"


def tasks_list(tasks: list[Assignment], completed_ids: set[int] | None = None) -> str:
    if completed_ids is None:
        completed_ids = set()

    all_done = all(task.task_id in completed_ids for task in tasks)
    lines = ["📋 Estas son tus tareas para hoy:"]
    for task in tasks:
        if task.task_id in completed_ids:
            lines.append(f"- ✅ {task.task_name} ({task.points} pts)")
        else:
            lines.append(f"- ⭕ {task.task_name} ({task.points} pts)")

    if all_done:
        lines.extend(["", "🎉 ¡Completaste todas tus tareas! ¡Felicitaciones! 👏"])
    else:
        lines.extend(
            [
                "",
                "👉 Presiona el botón o envía el nombre de una tarea para marcarla como realizada.",
            ]
        )

    return "\n".join(lines)


def balance(month: str, data: dict[str, int], names: dict[str, str]) -> str:
    lines = [f"📊 Balance del {month}:"]
    sorted_items = sorted(data.items(), key=lambda x: -x[1])
    if not sorted_items:
        lines.append("No hay datos disponibles.")
        return "\n".join(lines)

    max_points = sorted_items[0][1]
    for user_id, points in sorted_items:
        name = names.get(user_id, user_id)
        emoji = "🥇" if points == max_points and points > 0 else "💩"
        lines.append(f"{emoji} {name}: {points} pts")
    return "\n".join(lines)
