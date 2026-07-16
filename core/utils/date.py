import re

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from core.config import TZ


ISO_DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DAYS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
MONTHS = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]


def get_now() -> datetime:
    return datetime.now(ZoneInfo(TZ))


def get_today() -> date:
    return datetime.now(ZoneInfo(TZ)).date()


def format_date(iso_date: str) -> str:
    d = datetime.strptime(iso_date, "%Y-%m-%d")
    return d.strftime("%d/%m/%Y")


def format_date_short(iso_date: str) -> str:
    d = datetime.strptime(iso_date, "%Y-%m-%d")
    return f"{DAYS[d.weekday()]} {d.day:02d}"


def to_db_date(d: date) -> str:
    return d.isoformat()


def is_isoformat_date(value: str) -> bool:
    if not ISO_DATE_REGEX.match(value):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def next_due_date(base: date, frequency_days: int) -> str:
    return (base + timedelta(days=frequency_days)).isoformat()


def month_key(d: date) -> str:
    return d.strftime("%Y-%m")
