import argparse
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_DB = "~/apps/home-os/data/homeos.db"
DEFAULT_BACKUP_DIR = "~/backups/homeos"
DEFAULT_RETENTION_DAYS = 7


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def _require_env(name: str) -> str:
    value = _env(name)
    if not value:
        print(f"Error: environment variable '{name}' is not set.", file=sys.stderr)
        raise SystemExit(1)
    return value


def _ssh_target() -> str:
    host = _require_env("RPI_HOST")
    user = _require_env("RPI_USER")
    return f"{user}@{host}"


def _ssh_key() -> str:
    key = _require_env("RPI_SSH_KEY")
    path = Path(key).expanduser()
    if not path.exists():
        print(f"Error: SSH key '{path}' does not exist.", file=sys.stderr)
        raise SystemExit(1)
    return str(path)


def _find_executable(name: str) -> str:
    if os.name != "nt":
        return name
    windir = os.environ.get("WINDIR", r"C:\Windows")
    candidates = []
    if sys.maxsize <= 2**32:
        candidates.append(os.path.join(windir, "Sysnative", "OpenSSH", f"{name}.exe"))
    candidates.append(os.path.join(windir, "System32", "OpenSSH", f"{name}.exe"))
    found = shutil.which(name)
    if found:
        candidates.append(found)
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return name


def _run_remote(key: str, target: str, command: str) -> str:
    result = subprocess.run(
        [_find_executable("ssh"), "-i", key, target, command],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Error: remote command failed.", file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        raise SystemExit(1)
    return result.stdout


def _run_local(command: str) -> str:
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Error: local command failed.", file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        raise SystemExit(1)
    return result.stdout


def _build_backup_script(remote_db: str, backup_dir: str, retention_days: int, label: str) -> str:
    db = shlex.quote(str(Path(remote_db).expanduser()))
    directory = shlex.quote(str(Path(backup_dir).expanduser()))

    return (
        "set -e\n"
        "command -v sqlite3 >/dev/null 2>&1"
        " || { echo \"Error: sqlite3 is not installed.\" >&2; exit 1; }\n"
        f"mkdir -p {directory}\n"
        "stamp=$(date +%Y%m%d_%H%M%S)\n"
        f"backup={directory}/homeos_$stamp.db\n"
        f"sqlite3 {db} \".backup $backup\"\n"
        f"find {directory} -name 'homeos_*.db' -type f -mtime +{retention_days} -delete\n"
        f"echo \"{label}: $backup\"\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Back up the HomeOS DB on the Raspberry Pi")
    parser.add_argument(
        "--remote-db",
        default=_env("RPI_DB_PATH") or DEFAULT_DB,
        help=f"Remote DB path (default: {DEFAULT_DB})",
    )
    parser.add_argument(
        "--backup-dir",
        default=_env("RPI_BACKUP_DIR") or DEFAULT_BACKUP_DIR,
        help=f"Backup directory (default: {DEFAULT_BACKUP_DIR})",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=int(_env("RPI_BACKUP_RETENTION_DAYS") or DEFAULT_RETENTION_DAYS),
        help=f"Retention days (default: {DEFAULT_RETENTION_DAYS})",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Run the backup locally on the Raspberry Pi instead of over SSH",
    )
    args = parser.parse_args()

    if args.retention_days < 0:
        parser.error("--retention-days must be >= 0")

    script = _build_backup_script(
        args.remote_db,
        args.backup_dir,
        args.retention_days,
        "Backup completed" if args.local else "Remote backup completed",
    )

    if args.local:
        print("Running local backup...")
        output = _run_local(script)
    else:
        key = _ssh_key()
        target = _ssh_target()

        print(f"Checking SSH connection to {target}...")
        _run_remote(key, target, "echo ok")
        print("SSH connection OK.")

        print("Running remote backup...")
        output = _run_remote(key, target, script)

    if output:
        print(output.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
