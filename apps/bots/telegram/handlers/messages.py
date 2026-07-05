from datetime import date

from telegram import Update
from telegram.ext import ContextTypes

from apps.bots.telegram.formatters import format_mark_done, format_morning_message
from core.identity import get_user_by_chat_id
from modules.tasks.service import get_daily_assignments, mark_task_done
from modules.tasks.types import Assignment


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Escribe el nombre de la tarea cuando la completes. "
        "Usa /balance para ver puntos."
    )


async def _mark_task_done(task_name: str, chat_id: str) -> str:
    user = get_user_by_chat_id(chat_id)
    if user is None:
        return "No te reconozco. Pide a un admin que agregue tu chat_id al seed."
    
    result = mark_task_done(task_name, user.id, date.today())
    return format_mark_done(result)


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    message = await _mark_task_done(update.message.text, chat_id)
    await update.message.reply_text(message)


async def on_task_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    chat_id = str(query.from_user.id)
    _, task_name = query.data.split("|")
    
    user = get_user_by_chat_id(chat_id)
    if user is None:
        await query.edit_message_text("No te reconozco.")
        return
    
    if "completed_tasks" not in context.user_data:
        context.user_data["completed_tasks"] = set()
    
    today = date.today()
    assignments = get_daily_assignments(today)
    task_id = None
    for task in assignments:
        if task.task_name == task_name and task.assignee_user_id == user.id:
            task_id = task.task_id
            break
    
    if task_id is None:
        await query.edit_message_text("No encontré esa tarea.")
        return
    
    result = await _mark_task_done(task_name, chat_id)
    if "Listo:" in result:
        context.user_data["completed_tasks"].add(task_id)
    
    completed_ids = context.user_data.get("completed_tasks", set())
    tasks: list[Assignment] = [t for t in assignments if t.assignee_user_id == user.id]
    
    updated_message = format_morning_message(user.name, tasks, completed_ids)
    await query.edit_message_text(updated_message)
    await query.message.reply_text(result)
