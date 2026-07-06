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

## Deploy en Fly.io

El bot corre con webhook sobre un server Starlette + uvicorn que expone dos
rutas:

- `POST /telegram` — recibe los updates de Telegram (validado con el header
  `secret_token`).
- `GET|POST /trigger-daily/<WEBHOOK_SECRET>` — dispara el aviso diario. Lo llama
  un cron externo, no un scheduler en proceso.

Para abaratar, la máquina se apaga sola cuando no hay tráfico
(`auto_stop_machines = 'stop'`, `min_machines_running = 0`) y Fly la vuelve a
prender con cada request entrante (mensaje de Telegram o el cron). Así solo se
paga cómputo cuando el bot se usa, más el volumen (~USD 0.15/mes).

### Setup

```bash
fly launch --no-deploy                                 # crea la app desde el fly.toml
fly volumes create homeos_data --region gru --size 1   # volumen persistente para la DB
fly secrets set \
  TELEGRAM_BOT_TOKEN=... \
  WEBHOOK_SECRET=$(openssl rand -hex 32) \
  WEBHOOK_URL=https://home-os-maristian.fly.dev \
  ANTONIA_TELEGRAM_CHAT_ID=... \
  SEBASTIAN_TELEGRAM_CHAT_ID=...
fly deploy
```

`WEBHOOK_URL` es la URL pública de la app y `WEBHOOK_SECRET` valida los requests
(sirve tanto para el header de Telegram como para el token del cron).

### Cron del aviso diario

Configurar un cron externo (ej. cron-job.org) que haga un `POST` a las 8am hora
Chile:

```
https://home-os-maristian.fly.dev/trigger-daily/<WEBHOOK_SECRET>
```

Ojo con la zona horaria del cron: 8am en Chile es 11:00/12:00 UTC según horario
de verano. En cron-job.org se puede fijar `America/Santiago` directo.

## Contrato

API acordada entre la lógica de tareas y el bot. No se cambia sin conversarlo.

```python
def get_daily_assignments(day: date) -> list[Assignment]
def mark_task_done(text: str, user_id: str, day: date) -> MarkTaskResult
def get_month_balance(month: str) -> dict[str, int]

def notify(chat_id: str, message: str) -> None
```
