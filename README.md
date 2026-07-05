# home-os

## Desarrollo local

Requiere Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Antes de usar `docker-compose` copia el archivo de ejemplo de variables de entorno:

```bash
cp .env.example .env
```

Verifica que quedó bien:

```bash
python -c "import core, modules.tasks, apps.bots.telegram; print('imports OK')"
```

## Correr

```bash
python -m apps.bots.telegram.main
```