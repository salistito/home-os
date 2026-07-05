# home-os

## Desarrollo local

Requiere Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Verifica que quedó bien:

```bash
python -c "import core, modules.tasks, apps.bot; print('imports OK')"
```
