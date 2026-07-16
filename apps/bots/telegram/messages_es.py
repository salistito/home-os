from textwrap import dedent

from core.utils.date import MONTHS, format_date
from modules.reminders.types import Reminder, ReminderRecurrence
from modules.tasks.types import Assignment, Task

_RECURRENCE_LABELS = {
    "daily": "Diariamente",
    "weekly": "Semanalmente",
    "monthly": "Mensualmente",
    "yearly": "Anualmente",
}


def _format_recurrence(recurrence: str) -> str:
    if recurrence == "none":
        return "Sin recurrencia"
    return _RECURRENCE_LABELS.get(recurrence, recurrence.capitalize())


def _indent(text: str, value: int = 14) -> str:
    indentation = " " * value
    return text.replace("\n", "\n" + indentation)


def start_welcome() -> str:
    return dedent("""
        ¡Bienvenido/a a HomeOS! 🏠

        Organiza las tareas de tu hogar y gana puntos por completarlas. 🏆

        💻 Comandos principales:
          • 🗂️ /tasks - Crea y edita tus tareas
             recurrentes o ocasionales.
          • 📋 /assignments - Ver tus tareas
             asignadas para hoy.
          • 📊 /balance - Ver tus puntos
             acumulados durante el mes.
          • 🔔 /reminders - Administra tus
             recordatorios.

        💡 Vuelve a ver este mensaje con /help.
    """).strip()


def user_not_registered() -> str:
    return dedent("""
        ❌ Aún no estás registrado.

        👉 Ejecuta /users para registrarte.
    """).strip()


def tasks_crud_explanation() -> str:
    return dedent("""
        ⚙️ Gestión de tareas
        
        Las tareas son actividades del hogar
        que se asignan entre sus integrantes
        para mantenerlo organizado. 🧹
        
        Cada tarea otorga una cantidad de puntos
        al usuario que la complete. 🏆
        
        Puedes definir dos tipos de tareas:
        
        1) 🔁 Recurrentes
          • Se asignan automáticamente.
          • Se repiten según una frecuencia.
          • Ejemplo: Lavar la loza <b>cada</b> 2 días.
        
        2) 📌 Ocasionales
          • No se asignan automáticamente.
          • No tienen una frecuencia fija.
          • Ejemplo: Sacar la basura <b>cuando</b> el
            basurero esté lleno.
          
        💻 Comandos disponibles:
        
        ➕ Crear una tarea
          • /add_task &lt;name&gt; &lt;points&gt; [freq]
        
        🗂️ Ver todas las tareas
          • /list_tasks
        
        ✏️ Editar una tarea
          • /edit_task &lt;name&gt; &lt;field&gt; &lt;value&gt;
        
        🗑️ Eliminar una tarea
          • /delete_task &lt;name&gt;
          
        💡 Puedes ejecutar cualquiera de estos
        comandos sin parámetros para obtener
        más información sobre sus instrucciones.
    """).strip()


def add_task_usage() -> str:
    task1 = Task(id=1, name="Lavar la loza", points=3, frequency_days=2, next_due_date=None)
    task2 = Task(id=2, name="Sacar la basura", points=1, frequency_days=None, next_due_date=None)
    return dedent(f"""
        📝 Instrucciones comando /add_task

        📌 Propósito:
          • Crea una nueva tarea con puntos
            y una frecuencia opcional.

        💻 Sintaxis:
          • /add_task <name> <points> [freq]

        🧩 Parámetros:
          • 📋 name: Nombre de la tarea.
          • ⭐ points: Puntos que otorga.
          • 🔁 freq: Frecuencia en días (opcional).
             Si se omite, la tarea será ocasional.

        💡 Ejemplos

          1) ➡️ /add_task Lavar la loza 3 2
              {_indent(task_created(task1))}

          2) ➡️ /add_task Sacar la basura 1
              {_indent(task_created(task2))}
    """).strip()


def list_tasks(tasks: list[Task]) -> str:
    if not tasks:
        return dedent("""
            📭 No hay tareas registradas.

            👉 Crea tu primera tarea ejecutando el comando /add_task
        """).strip()
    lines = ["🗂️ Catálogo de tareas", ""]
    for t in tasks:
        freq = f"Cada {t.frequency_days} días" if t.frequency_days else "Ocasional"
        due_date = format_date(t.next_due_date) if t.next_due_date else "-"
        lines.append(f"{t.name}")
        lines.append(f"├ ⭐ Puntos: [{t.points} pts]")
        lines.append(f"├ 🔁 Frecuencia: {freq}")
        lines.append(f"└ 📅 Próxima ocurrencia: {due_date}")
        lines.append("")
    return "\n".join(lines).strip()


def edit_task_usage() -> str:
    return dedent(f"""
        📝 Instrucciones comando /edit_task

        📌 Propósito:
          • Edita un campo de una tarea existente.

        💻 Sintaxis:
          • /edit_task &lt;name&gt; &lt;field&gt; &lt;value&gt;

        🧩 Parámetros:
          • 📋 name: Nombre de la tarea.
          • 🏷️ field: Campo a modificar.
          • 💬 value: Nuevo valor.

        🏷️ Campos editables:
          • name → Cambia el nombre.
          • points → Cambia los puntos.
          • freq → Cambia la frecuencia.

        💡 Ejemplos

          1) Cambiar el <b>nombre</b>
              ➡️ /edit_task Barrer name Limpiar
              {_indent(task_updated("Barrer", "name", "Barrer", "Limpiar"))}

          2) Cambiar los <b>puntos</b>
              ➡️ /edit_task Lavar la loza points 6
              {_indent(task_updated("Lavar la loza", "points", "3", "6"))}

          3) Cambiar la <b>frecuencia</b>
              ➡️ /edit_task Lavar la loza freq 7
              {_indent(task_updated("Lavar la loza", "freq", "10", "7"))}
    """).strip()


def delete_task_usage() -> str:
    return dedent(f"""
        📝 Instrucciones comando /delete_task

        📌 Propósito:
          • Elimina una tarea existente.

        💻 Sintaxis:
          • /delete_task <name>

        🧩 Parámetros:
          • 📋 name: Nombre de la tarea.

        💡 Ejemplo

          1) ➡️ /delete_task Lavar la loza
              {_indent(task_deleted("Lavar la loza"))}
    """).strip()


def task_invalid_name() -> str:
    return "❌ Debes ingresar un nombre válido para la tarea."


def task_invalid_points() -> str:
    return "❌ Los puntos deben ser un número entero mayor que 0."


def task_invalid_frequency() -> str:
    return "❌ La frecuencia debe ser un número entero mayor que 0 (en días)."


def task_duplicate_name(task_name: str) -> str:
    return f"❌ Ya existe una tarea llamada '{task_name}'."


def task_has_assignments_error(task_name: str) -> str:
    return dedent(f"""
        ❌ No se puede eliminar
        '{task_name}'
        porque tiene asignaciones pendientes.
    """).strip()


def task_not_found_by_name(task_name: str) -> str:
    return f"❌ No encontré ninguna tarea llamada '{task_name}'."


def task_created(task: Task) -> str:
    freq = f"Cada {task.frequency_days} días" if task.frequency_days else "Ocasional"
    return dedent(f"""
        ✅ Tarea creada
          • {task.name}
            ├ ⭐ Puntos: [{task.points} pts]
            └ 🔁 Frecuencia: {freq}
    """).strip()


def task_updated(name: str, field: str, old_value: str, new_value: str) -> str:
    if field == "name":
        formatted_old = f"'{old_value}'"
        formatted_new = f"'{new_value}'"
    elif field == "points":
        formatted_old = f"[{old_value} pts]"
        formatted_new = f"[{new_value} pts]"
    else:
        formatted_old = "Ocasional" if str(old_value) in ("0", "Ocasional") else f"{old_value} días"
        formatted_new = "Ocasional" if str(new_value) in ("0", "Ocasional") else f"{new_value} días"
    return dedent(f"""
        ✏️ Tarea actualizada
          • {name if field != "name" else old_value}
            └ 🔄 {formatted_old} → {formatted_new}
    """).strip()


def task_deleted(task_name: str) -> str:
    return f"🗑️ Se eliminó la tarea: '{task_name}'."


def morning_message(
    user_name: str, assignments: list[Assignment], completed_ids: set[int] | None = None
) -> str:
    return f"🌅 ¡Buenos días, {user_name}!\n\n{assignments_list(assignments, completed_ids)}"


def assignments_list(assignments: list[Assignment], completed_ids: set[int] | None = None) -> str:
    if completed_ids is None:
        completed_ids = set()

    all_done = all(assignment.task_id in completed_ids for assignment in assignments)
    lines = ["📋 Tus tareas asignadas para hoy son:"]
    for assignment in assignments:
        if assignment.task_id in completed_ids:
            lines.append(f"  • ✅ {assignment.task_name} [{assignment.points} pts]")
        else:
            lines.append(f"  • ⭕ {assignment.task_name} [{assignment.points} pts]")

    if all_done:
        lines.extend(["", "🎉 ¡Completaste todas tus tareas! ¡Felicitaciones! 👏"])
    else:
        lines.extend(
            [
                "",
                "👉 Presiona el botón asociado a una tarea para registrarla como completada.",
            ]
        )

    return "\n".join(lines)


def no_assignments_today(user_name: str) -> str:
    return dedent(f"""
        🌅 ¡Buenos días, {user_name}!

        {no_pending_assignments()}
    """).strip()


def no_pending_assignments() -> str:
    return "🎉 No tienes tareas asignadas para hoy. ¡Disfruta el día! 😊"


def assignment_already_done(assignment_name: str) -> str:
    return f"ℹ️ Hoy ya se completó la tarea '{assignment_name}'."


def assignment_not_found(searched_text: str | None) -> str:
    if not searched_text:
        return "❌ No encontré esa tarea."
    return f"❌ No encontré ninguna tarea llamada '{searched_text}'."


def balance(month: str, data: dict[str, int], names: dict[str, str]) -> str:
    year, month_index = month.split("-")
    month_name = MONTHS[int(month_index) - 1]
    lines = [f"📊 Balance de {month_name} {year}:"]

    sorted_items = sorted(data.items(), key=lambda x: -x[1])
    if not sorted_items:
        lines.append("Aún no hay datos registrados. 😭")
        return "\n".join(lines)

    max_points = sorted_items[0][1]
    for user_id, points in sorted_items:
        name = names.get(user_id, user_id)
        emoji = "🥇" if points == max_points and points > 0 else "💩"
        lines.append(f"  • {emoji} {name} [{points} pts]")
    return "\n".join(lines)


def reminders_crud_explanation() -> str:
    return dedent("""
        ⚙️ Gestión de recordatorios
        
        Los recordatorios te permiten programar
        alertas para no olvidar eventos importantes. 🔔
        
        Puedes definir dos tipos de recordatorios:
        
        1) ⏰ Tiempo relativo
          • Se activa después de un período de tiempo.
          • Útil para alarmas a corto plazo.
          • Ejemplo: Colgar la ropa <b>en 3 horas</b>.
        
        2) 📅 Tiempo absoluto
          • Se activa en una fecha u hora específica.
          • Útil para eventos con fecha fija.
          • Ejemplo: Cumpleaños <b>el 14-11-2026</b>.
        
        Además, puedes configurar una recurrencia
        para que se repita automáticamente:
        diaria, semanal, mensual o anual. 🔁
          
        💻 Comandos disponibles:
        
        ➕ Crear un recordatorio
          • /add_reminder &lt;message&gt; &lt;relative_time&gt; [recurrence]
          • /add_reminder &lt;message&gt; &lt;date&gt; [time] [recurrence]
        
        🗂️ Ver recordatorios
          • /list_reminders
        
        ✏️ Editar un recordatorio
          • /edit_reminder &lt;message&gt; &lt;field&gt; &lt;value&gt;
        
        🗑️ Eliminar un recordatorio
          • /delete_reminder &lt;message&gt;
          
        💡 Puedes ejecutar cualquiera de estos
        comandos sin parámetros para obtener
        más información sobre sus instrucciones.
    """).strip()


def add_reminder_usage() -> str:
    reminder1 = Reminder(
        id=1,
        user_id="sebastian",
        message="Colgar la ropa",
        trigger_at="2026-07-14",
        trigger_time="12:00",
        recurrence=ReminderRecurrence.NONE,
        created_at="2026-07-13",
    )
    reminder2 = Reminder(
        id=2,
        user_id="sebastian",
        message="Comprar regalo",
        trigger_at="2026-12-07",
        recurrence=ReminderRecurrence.NONE,
        created_at="2026-07-13",
    )
    reminder3 = Reminder(
        id=3,
        user_id="sebastian",
        message="Tomar vitaminas",
        trigger_at="2026-07-14",
        trigger_time="09:00",
        recurrence=ReminderRecurrence.DAILY,
        created_at="2026-07-13",
    )
    return dedent(f"""
        📝 Instrucciones comando /add_reminder

        📌 Propósito:
          • Crea un recordatorio para
            una fecha u hora específica.

        💻 Sintaxis:
          • /add_reminder <message> <relative_time> [recurrence]
          • /add_reminder <message> <date> [time] [recurrence]

        🧩 Parámetros:
          • 📋 message: Mensaje del recordatorio.
          • ⏰ relative_time: Tiempo relativo.
             Formatos: 45m, 1h30m, 4h, 3d, 2w, 1y.
          • 📅 date: Fecha específica (YYYY-MM-DD).
          • 🕐 time: Hora específica, opcional (HH:MM).
          • 🔁 recurrence: Frecuencia (opcional).
             Valores: none, daily, weekly, monthly, yearly.
             Si se omite, se usa none.

        💡 Ejemplos

          1) ➡️ /add_reminder Colgar la ropa 3h
              {_indent(reminder_created(reminder1))}

          2) ➡️ /add_reminder Comprar regalo 2026-12-07
              {_indent(reminder_created(reminder2))}

          3) ➡️ /add_reminder Tomar vitaminas 2026-07-14 09:00 daily
              {_indent(reminder_created(reminder3))}
    """).strip()


def list_reminders(reminders: list[Reminder]) -> str:
    if not reminders:
        return "📭 No tienes recordatorios activos."
    lines = ["⏰ Recordatorios activos", ""]
    for r in reminders:
        time_part = f" {r.trigger_time}" if r.trigger_time else ""
        lines.append(f"{r.message}")
        lines.append(f"├ 📅 Fecha: {r.trigger_at}{time_part}")
        lines.append(f"└ 🔁 Recurrencia: {_format_recurrence(r.recurrence.value)}")
        lines.append("")
    return "\n".join(lines).strip()


def edit_reminder_usage() -> str:
    return dedent(f"""
        📝 Instrucciones comando /edit_reminder

        📌 Propósito:
          • Edita un campo de un recordatorio.

        💻 Sintaxis:
          • /edit_reminder &lt;message&gt; &lt;field&gt; &lt;value&gt;

        🧩 Parámetros:
          • 📋 message: Mensaje del recordatorio.
          • 🏷️ field: Campo a modificar.
          • 💬 value: Nuevo valor.

        🏷️ Campos editables:
          • message → Cambia el mensaje.
          • trigger_at → Cambia la fecha.
          • trigger_time → Cambia la hora.
          • recurrence → Cambia la recurrencia.

        💡 Ejemplos

          1) Cambiar el <b>mensaje</b>
              ➡️ /edit_reminder Cumpleaños Seba message Cumple Mari
              {_indent(reminder_updated("Cumpleaños Seba", "message", "Cumpleaños Seba", "Cumple Mari"))}

          2) Cambiar la <b>fecha</b>
              ➡️ /edit_reminder Cumple Mari trigger_at 2026-12-07
              {_indent(reminder_updated("Cumple Mari", "trigger_at", "2026-11-14", "2026-12-07"))}

          3) Cambiar la <b>hora</b>
              ➡️ /edit_reminder Cumple Mari trigger_time 08:30
              {_indent(reminder_updated("Cumple Mari", "trigger_time", "00:00", "08:30"))}

          4) Cambiar la <b>recurrencia</b>
              ➡️ /edit_reminder Cumple Mari recurrence yearly
              {_indent(reminder_updated("Cumple Mari", "recurrence", "none", "yearly"))}
    """).strip()


def delete_reminder_usage() -> str:
    return dedent(f"""
        📝 Instrucciones comando /delete_reminder

        📌 Propósito:
          • Elimina un recordatorio.

        💻 Sintaxis:
          • /delete_reminder <message>

        🧩 Parámetros:
          • 📋 message: Mensaje del recordatorio.

        💡 Ejemplo

          1) ➡️ /delete_reminder Cita romántica
              {_indent(reminder_deleted("Cita romántica"))}
    """).strip()


def reminder_invalid() -> str:
    return "❌ Datos inválidos."


def reminder_invalid_message() -> str:
    return "❌ Debes ingresar un mensaje válido para el recordatorio."


def reminder_invalid_time() -> str:
    return dedent("""
        ❌ Formato de tiempo inválido.
        Usa: 45m, 1h30m, 4h, 3d, 2w, 1y,
        YYYY-MM-DD o YYYY-MM-DD HH:MM
    """).strip()


def reminder_invalid_date() -> str:
    return dedent("""
        ❌ Formato de fecha inválido.
        Usa: YYYY-MM-DD o YYYY-MM-DD HH:MM
    """).strip()


def reminder_invalid_recurrence() -> str:
    return "❌ La recurrencia debe ser: none, daily, weekly, monthly o yearly."


def reminder_past_time() -> str:
    return "❌ No se puede programar un recordatorio en el pasado."


def reminder_duplicate_message(reminder_message: str) -> str:
    return f"❌ Ya existe un recordatorio con el mensaje '{reminder_message}'."


def reminder_not_found_by_message(reminder_message: str) -> str:
    return f"❌ No encontré ningún recordatorio con el mensaje '{reminder_message}'."


def day_reminders_message(reminders: list[Reminder]) -> str:
    lines = ["⏰ Hoy me pediste que te recordara:"]
    for r in reminders:
        lines.append(f"  • 🔔 {r.message}")
    return "\n".join(lines)


def timed_reminder_message(reminder: Reminder) -> str:
    return f"🔔 Recordatorio: {reminder.message}"


def add_reminder_ask_message() -> str:
    return "📝 ¿Qué quieres que te recuerde?"


def add_reminder_ask_time() -> str:
    return "⏰ ¿Cuándo? (ej: 45m, 1h30m, 4h, 3d, 2w, 1y, YYYY-MM-DD, YYYY-MM-DD HH:MM)"


def add_reminder_ask_recurrence() -> str:
    return "🔁 ¿Cúal es su recurrencia? (none, daily, weekly, monthly, yearly)"


def edit_reminder_ask_message() -> str:
    return "✏️ ¿Qué recordatorio quieres editar?"


def edit_reminder_ask_field() -> str:
    return "🏷️ ¿Qué campo quieres editar? (message, trigger_at, trigger_time, recurrence)"


def edit_reminder_ask_value() -> str:
    return "💬 ¿Cuál es el nuevo valor?"


def delete_reminder_ask_message() -> str:
    return "🗑️ ¿Qué recordatorio quieres eliminar?"


def create_reminder_error() -> str:
    return "❌ No fue posible crear el recordatorio, inténtalo más tarde."


def reminder_created(reminder: Reminder) -> str:
    time_part = f" a las {reminder.trigger_time}" if reminder.trigger_time else ""
    return dedent(f"""
        ✅ Recordatorio creado
          • {reminder.message}
            ├ 📅 Fecha: {reminder.trigger_at}{time_part}
            └ 🔁 Recurrencia: {_format_recurrence(reminder.recurrence.value)}
    """).strip()


def reminder_updated(name: str, field: str, old_value: str, new_value: str) -> str:
    if field == "message":
        formatted_old = f"'{old_value}'"
        formatted_new = f"'{new_value}'"
    elif field == "trigger_at":
        formatted_old = format_date(old_value)
        formatted_new = format_date(new_value)
    elif field == "recurrence":
        formatted_old = _format_recurrence(old_value)
        formatted_new = _format_recurrence(new_value)
    else:
        formatted_old = old_value
        formatted_new = new_value
    return dedent(f"""
        ✏️ Recordatorio actualizado
          • {name if field != "message" else old_value}
            └ 🔄 {formatted_old} → {formatted_new}
    """).strip()


def reminder_deleted(reminder_message: str) -> str:
    return f"🗑️ Se eliminó el recordatorio: '{reminder_message}'."
