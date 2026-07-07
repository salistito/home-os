from modules.tasks.types import Assignment


def start_welcome() -> str:
    return (
        "👋 ¡Hola! Bienvenido/a a HomeOS:\nEl sistema para organizar tu hogar. 🏠\n\n"
        "🎯 Aquí podrás gestionar tus tareas diarias y sumar puntos por cumplirlas. 🏆\n\n"
        "📋 Usa /assignments para ver tus tareas asignadas para el día.\n"
        "📝 Presiona el botón de una tarea o envía su nombre para marcarla como realizada.\n"
        "📊 Usa /balance para ver tus puntos acumulados durante el mes.\n\n"
        "💡 Puedes volver a ver este mensaje ejecutando el comando /start o /help.\n\n"
        "¡Mucha suerte! 💪"
    )


def user_not_registered() -> str:
    return "❌ No estás registrado. Pídele a un administrador que registre tu chat_id en la aplicación."


def assignment_not_found(searched_text: str | None) -> str:
    if not searched_text:
        return "❌ No encontré esa tarea"
    return f"❌ No encontré la tarea '{searched_text}'"


def assignment_already_done(assignment_name: str) -> str:
    return f"ℹ️ Hoy ya se completó la tarea '{assignment_name}'"


def assignments_updated() -> str:
    return "✨ Tareas actualizadas correctamente"


def no_pending_assignments() -> str:
    return "🎉 No tienes tareas pendientes para hoy. ¡Disfruta el día! 😊"


def no_assignments_today(user_name: str) -> str:
    return f"🌅 ¡Buenos días, {user_name}!\n\n{no_pending_assignments()}"


def morning_message(
    user_name: str, assignments: list[Assignment], completed_ids: set[int] | None = None
) -> str:
    return f"🌅 ¡Buenos días, {user_name}!\n\n{assignments_list(assignments, completed_ids)}"


def assignments_list(assignments: list[Assignment], completed_ids: set[int] | None = None) -> str:
    if completed_ids is None:
        completed_ids = set()

    all_done = all(assignment.task_id in completed_ids for assignment in assignments)
    lines = ["📋 Estas son tus tareas para hoy:"]
    for assignment in assignments:
        if assignment.task_id in completed_ids:
            lines.append(f"- ✅ {assignment.task_name} ({assignment.points} pts)")
        else:
            lines.append(f"- ⭕ {assignment.task_name} ({assignment.points} pts)")

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
