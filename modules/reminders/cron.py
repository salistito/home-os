import httpx
import logging

from datetime import datetime

from core.config import CRONJOB_ORG_API_KEY, TZ, WEBHOOK_URL, WEBHOOK_SECRET

# cron-job.org REST API docs: https://docs.cron-job.org/rest-api.html
# Authentication: Bearer token via CRONJOB_ORG_API_KEY env var.
# Rate limit: 100 requests/day (free), 5,000/day (sustaining member).

_API_BASE = "https://api.cron-job.org"
logger = logging.getLogger(__name__)


def _build_callback_url() -> str:
    """
    Build the URL that cron-job.org will GET when a job fires.

    The endpoint /trigger_timed_reminders/{token} is defined in apps/bots/telegram/main.py
    and sends due timed reminders via Telegram.
    """
    return f"{WEBHOOK_URL.rstrip('/')}/trigger_timed_reminders/{WEBHOOK_SECRET}"


def _to_expires_at(trigger_at: str, trigger_time: str) -> int:
    """
    Convert trigger date/time to cron-job.org expiresAt format (YYYYMMDDhhmmss).

    cron-job.org stops scheduling a job after expiresAt (this is call one-shot job).
    We set it to trigger_time + 1 minute so the job has a window to fire exactly at trigger_time, then expires.
    """
    dt = datetime.strptime(f"{trigger_at} {trigger_time}", "%Y-%m-%d %H:%M")
    dt_plus = (
        dt.replace(minute=dt.minute + 1)
        if dt.minute < 59
        else dt.replace(hour=dt.hour + 1, minute=0)
    )
    return int(dt_plus.strftime("%Y%m%d%H%M%S"))


def _build_schedule(trigger_at: str, trigger_time: str) -> dict:
    """
    Build the schedule object for cron-job.org API.

    cron-job.org doesn't accept a single datetime; instead it expects each component
    (hour, minute, day of month, month, day of week) as separate arrays.
    We set wdays to [-1] (every day) since the exact day is already specified via mdays + months.

    See: https://docs.cron-job.org/rest-api.html#jobschedule
    """
    dt = datetime.strptime(f"{trigger_at} {trigger_time}", "%Y-%m-%d %H:%M")
    return {
        "timezone": TZ,
        "expiresAt": _to_expires_at(trigger_at, trigger_time),
        "hours": [dt.hour],
        "minutes": [dt.minute],
        "mdays": [dt.day],
        "months": [dt.month],
        "wdays": [-1],
    }


def create_one_shot_job(trigger_at: str, trigger_time: str) -> str | None:
    """
    Create a one-shot cron job on cron-job.org.

    Uses PUT /jobs to create a job that fires once at trigger_at + trigger_time, then expires.
    Returns the job ID on success, or None on failure (API not configured, network error, etc.).

    API docs: https://docs.cron-job.org/rest-api.html#creating-a-cron-job
    Rate limit: max 1 request/second, 5 requests/minute.
    """
    if not CRONJOB_ORG_API_KEY or not WEBHOOK_URL or not WEBHOOK_SECRET:
        logger.warning("cron-job.org not configured, skipping job creation")
        return None

    payload = {
        "job": {
            "url": _build_callback_url(),
            "enabled": True,
            "saveResponses": False,
            "requestMethod": 0,  # GET
            "schedule": _build_schedule(trigger_at, trigger_time),
        }
    }

    try:
        resp = httpx.put(
            f"{_API_BASE}/jobs",
            json=payload,
            headers={
                "Authorization": f"Bearer {CRONJOB_ORG_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        resp.raise_for_status()
        job_id = str(resp.json()["jobId"])
        logger.info("Created cron-job.org job %s for %s %s", job_id, trigger_at, trigger_time)
        return job_id
    except Exception:
        logger.exception("Failed to create cron-job.org job for %s %s", trigger_at, trigger_time)
        return None


def update_job(job_id: str, trigger_at: str, trigger_time: str) -> bool:
    """
    Update the schedule of an existing cron job on cron-job.org.

    Uses PATCH /jobs/{jobId} with only the new schedule. This is preferred over
    delete + create when the job already exists, since it preserves the same jobId.

    API docs: https://docs.cron-job.org/rest-api.html#updating-a-cron-job
    Rate limit: max 5 requests/second.
    """
    if not CRONJOB_ORG_API_KEY:
        return False

    payload = {"job": {"schedule": _build_schedule(trigger_at, trigger_time)}}

    try:
        resp = httpx.patch(
            f"{_API_BASE}/jobs/{job_id}",
            json=payload,
            headers={
                "Authorization": f"Bearer {CRONJOB_ORG_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        resp.raise_for_status()
        logger.info("Updated cron-job.org job %s to %s %s", job_id, trigger_at, trigger_time)
        return True
    except Exception:
        logger.exception("Failed to update cron-job.org job %s", job_id)
        return False


def delete_job(job_id: str) -> bool:
    """
    Delete a cron job from cron-job.org by its ID.

    Uses DELETE /jobs/{jobId}. Returns True on success, False on failure.
    Failing to delete is non-critical (the job will just expire on its own via expiresAt).

    API docs: https://docs.cron-job.org/rest-api.html#deleting-a-cron-job
    Rate limit: max 5 requests/second.
    """
    if not CRONJOB_ORG_API_KEY:
        return False

    try:
        resp = httpx.delete(
            f"{_API_BASE}/jobs/{job_id}",
            headers={
                "Authorization": f"Bearer {CRONJOB_ORG_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        resp.raise_for_status()
        logger.info("Deleted cron-job.org job %s", job_id)
        return True
    except Exception:
        logger.exception("Failed to delete cron-job.org job %s", job_id)
        return False
