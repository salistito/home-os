import stat

from pathlib import Path


HOOKS_DIR = Path(__file__).resolve().parent.parent / ".git" / "hooks"
PRE_PUSH = HOOKS_DIR / "pre-push"

HOOK_CONTENT = r"""#!/bin/bash
set -e

echo "Running ruff..."
.venv/bin/ruff check . || { echo "Ruff failed. Fix lint errors before pushing."; exit 1; }

echo "Running tests with coverage (min 95%)..."
.venv/bin/python -m pytest --cov=core --cov=modules --cov=apps --cov-report=term-missing --cov-fail-under=95 || {
  echo "Tests failed or coverage below 95%. Fix before pushing."
  exit 1
}

echo "All checks passed."
"""


def main():
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    PRE_PUSH.write_text(HOOK_CONTENT, encoding="utf-8")
    PRE_PUSH.chmod(PRE_PUSH.stat().st_mode | stat.S_IEXEC)
    print("pre-push hook installed.")


if __name__ == "__main__":
    main()
