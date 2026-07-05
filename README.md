# HomeOS

Bot de Telegram para repartir las tareas de la casa entre dos o más personas.
En la mañana avisa a cada quien qué le toca; cuando respondes que la hiciste,
suma puntos y lleva un balance mensual.

## Estructura

- `core/` — compartido: base de datos, identidad, notificaciones.
- `modules/` — lógica de dominio (tareas, puntos). Usa `core/`.
- `apps/` — apps ejecutables (el bot de Telegram). Usa `core/` y `modules/`.

`core/` no importa de `modules/` ni `apps/`.

## Desarrollo local

Requiere Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Verifica que quedó bien:

```bash
python -c "import core, modules.tasks, apps.bots.telegram; print('imports OK')"
```

Correr:

```bash
python -m apps.bots.telegram.main
```

Crea la base de datos SQLite (por defecto `./homeos.db`) e imprime `DB lista`.
El archivo `.db` es local y no se versiona; se regenera solo al arrancar.

## Docker

```bash
cp .env.example .env   # completa TELEGRAM_BOT_TOKEN
docker compose up --build
```

La base de datos persiste en `./data` gracias al volumen del `docker-compose.yml`.

## Contrato

API acordada entre la lógica de tareas y el bot. No se cambia sin conversarlo.

```python
def get_daily_assignments(day: date) -> list[Assignment]
def mark_task_done(text: str, user_id: str, day: date) -> MarkTaskResult
def get_month_balance(month: str) -> dict[str, int]

def notify(chat_id: str, message: str) -> None
```
