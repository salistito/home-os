# HomeOS

Bot de Telegram para repartir las tareas de la casa entre dos o más personas. Cada mañana asigna las tareas del día al miembro con menos puntos acumulados en el mes, y al completarlas se suman puntos para llevar un balance mensual.

## Arquitectura

El proyecto sigue una arquitectura en capas con dependencia unidireccional:

```
apps/bots/telegram/   ← entrypoint del bot (Starlette + python-telegram-bot)
  │
modules/tasks/        ← lógica de dominio (servicios, repositorio, tipos)
  │
core/                 ← infraestructura compartida (DB, config, identidad, notificaciones)
```

Reglas de dependencia:
- `core/` **no puede** importar de `modules/` ni `apps/`.
- `modules/` puede importar solo de `core/`.
- `apps/` puede importar de ambos.

### core/

| Archivo | Propósito |
|---|---|
| `config.py` | Carga variables de entorno desde `.env` usando `python-dotenv` |
| `db.py` | Conexión SQLite con `row_factory = sqlite3.Row` y `PRAGMA foreign_keys = ON` |
| `schema.sql` | Esquema de la base de datos (`users`, `tasks`, `assignments`) |
| `identity.py` | Consulta de usuarios desde la DB |
| `notifications.py` | Envío de mensajes a Telegram via `urllib` (no usa python-telegram-bot) |
| `seed.py` | Carga datos iniciales desde archivos YAML en `seed/` |

### modules/tasks/

| Archivo | Propósito |
|---|---|
| `types.py` | Dataclasses: `Task`, `Assignment`, `AssignmentCompletionResult` and enums: `AssignmentCompletionStatus` |
| `repository.py` | Consultas SQL (tasks, assignments, puntos por usuario) |
| `service.py` | Lógica de negocio: asignar tareas, marcar como hechas, balance mensual |

### apps/bots/telegram/

| Archivo | Propósito |
|---|---|
| `main.py` | Punto de entrada: servidor Starlette + Uvicorn, rutas webhook |
| `app.py` | Construcción de la aplicación `python-telegram-bot` con handlers |
| `jobs.py` | Envío de asignaciones diarias a cada usuario |
| `messages_es.py` | Mensajes de texto en español (i18n listo para agregar otros idiomas) |
| `trigger_daily.py` | Script CLI para ejecutar asignaciones diarias sin servidor web |
| `handlers/commands.py` | Comandos `/start`, `/help`, `/balance`, `/assignments` |
| `handlers/messages.py` | Mensajes de texto y botones inline |

## Requisitos

- Python 3.12 o superior
- Un bot de Telegram (crear con [@BotFather](https://t.me/BotFather))
- (Opcional) Docker

## Configuración inicial

1. Clona el repositorio y crea un entorno virtual:

```bash
git clone <repo>
cd home-os
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

2. Instala el proyecto en modo editable con dependencias de desarrollo:

```bash
pip install -e ".[dev]"
```

3. Copia el archivo de ejemplo y completa las variables:

```bash
cp .env.example .env
```

Edita `.env` con los siguientes valores:

| Variable | Descripción |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token del bot (de @BotFather) |
| `SEBASTIAN_TELEGRAM_CHAT_ID` | Chat ID del primer integrante |
| `ANTONIA_TELEGRAM_CHAT_ID` | Chat ID del segundo integrante |
| `WEBHOOK_URL` | URL pública del bot (para webhook) |
| `WEBHOOK_SECRET` | Token aleatorio para validar requests |

> Para obtener tu `chat_id`, envía un mensaje a [@userinfobot](https://t.me/userinfobot) en Telegram.

### Variables de entorno

| Variable | Defecto | Descripción |
|---|---|---|
| `HOME_OS_DB_PATH` | `./homeos.db` | Ruta al archivo SQLite |
| `HOME_OS_SEED_PATH` | `./core/seed.yaml` | Ruta al archivo de seed (ya no se usa, el seed está en `seed/`) |
| `TZ` | `America/Santiago` | Zona horaria |
| `PORT` | `8080` | Puerto del servidor webhook |

## Ejecución local

```bash
python -m apps.bots.telegram.main
```

Si `WEBHOOK_URL` y `WEBHOOK_SECRET` están configurados, levanta un servidor Starlette + Uvicorn en `http://0.0.0.0:8080` en modo webhook.  
Si no, arranca en **modo polling** — el bot escucha actualizaciones de Telegram sin necesidad de un servidor accesible públicamente.

### Asignación diaria sin servidor web

Para probar o ejecutar la rutina de asignación diaria localmente sin levantar el bot ni configurar un cron:

```bash
python -m apps.bots.telegram.trigger_daily
```

Esto inicializa la base de datos, ejecuta el mismo algoritmo de asignación que usa el cron en producción y envía los mensajes por Telegram a cada integrante.

### Verificar instalación

```bash
python -c "import core, modules.tasks, apps.bots.telegram; print('imports OK')"
```

### Linter

```bash
ruff check .
```

No hay typechecker configurado. Ruff usa `line-length = 100`.

## Seed data

Al arrancar, el bot inicializa la DB y carga datos desde `seed/`:

### `seed/users.yaml`

Define los integrantes de la casa. El `telegram_chat_id` soporta expansión de variables de entorno con sintaxis `$VAR_NAME`:

```yaml
users:
  - id: sebastian
    name: Sebastian
    telegram_chat_id: $SEBASTIAN_TELEGRAM_CHAT_ID
  - id: antonia
    name: Antonia
    telegram_chat_id: $ANTONIA_TELEGRAM_CHAT_ID
```

### `seed/tasks.yaml`

Define las tareas del hogar. Cada tarea puede ser:

- **Recurrente** (con `frequency_days`): se asigna automáticamente cada N días. El `next_due_date` se calcula desde hoy más `start_offset_days`.
- **Ocasional** (sin `frequency_days`): los integrantes la marcan como hecha cuando quieran.

```yaml
tasks:
  - name: lavar la loza
    points: 3
    frequency_days: 2
    start_offset_days: 1
  - name: sacar reciclaje
    points: 2
```

Las tareas se cargan una sola vez (si el nombre ya existe en la DB, se salta).

## Uso del bot

| Comando / Acción | Descripción |
|---|---|
| `/start` | Mensaje de bienvenida con instrucciones |
| `/balance` | Muestra los puntos acumulados este mes |
| `/assignments` | Muestra las tareas pendientes de hoy con botones |
| `Escribir nombre de tarea` | Marca una tarea como completada (coincidencia exacta, case-insensitive) |
| Botón inline | Marca la tarea como completada desde el mensaje de la mañana |

### ¿Cómo funciona la asignación diaria?

1. Se marcan como `failed` las tareas pendientes de días anteriores.
2. Se buscan tareas recurrentes cuya `next_due_date` sea hoy o anterior, ordenadas por puntos de mayor a menor.
3. Se asignan al integrante con **menos puntos acumulados en el mes actual**. En caso de empate, se elige al azar.
4. Cada integrante tiene un **tope diario de puntos** igual a `1.5 × la tarea con más puntos del día`. Al alcanzarlo, no recibe más tareas ese día. Las tareas que nadie puede tomar se saltan y quedan pendientes para el próximo ciclo.
5. Se envía un mensaje a cada integrante con sus tareas y botones para marcar como hecha.
6. Al marcar como hecha, se recalcula `next_due_date = today + frequency_days`.

## Docker

```bash
cp .env.example .env
# completa TELEGRAM_BOT_TOKEN y los chat IDs
docker compose up --build
```

La base de datos persiste en `./data` gracias al volumen definido en `docker-compose.yml`.

## Contrato de la API

La interfaz entre la lógica de dominio (`modules/tasks/service.py`) y el bot. No se cambia sin conversarlo.

```python
def get_daily_assignments(day: date) -> list[Assignment]

def mark_assignment_done(text: str, user_id: str, day: date) -> AssignmentCompletionResult

def get_month_balance(month: str) -> dict[str, int]
```

Notificaciones (desde `core/notifications.py`):

```python
def notify(chat_id: str, message: str) -> None
```

## Producción (Fly.io)

El bot corre en modo webhook sobre Starlette + Uvicorn con dos rutas:

- `POST /telegram` — recibe updates de Telegram (validado con header `X-Telegram-Bot-Api-Secret-Token`).
- `GET|POST /trigger-daily/<WEBHOOK_SECRET>` — dispara la asignación diaria. Lo llama un cron externo.

La máquina de Fly.io se apaga automáticamente sin tráfico (`auto_stop_machines = 'stop'`, `min_machines_running = 0`) y arranca con cada request entrante. Así solo se paga el cómputo cuando el bot está activo (~USD 0.15/mes por el volumen).

### Setup inicial en Fly.io

```bash
fly launch --no-deploy
fly volumes create homeos_data --region gru --size 1
fly secrets set \
  TELEGRAM_BOT_TOKEN=<token> \
  WEBHOOK_SECRET=$(openssl rand -hex 32) \
  WEBHOOK_URL=https://<tu-app>.fly.dev \
  ANTONIA_TELEGRAM_CHAT_ID=<chat_id> \
  SEBASTIAN_TELEGRAM_CHAT_ID=<chat_id>
fly deploy
```

### Cron del aviso diario

Configurar un cron externo (ej. [cron-job.org](https://cron-job.org)) que haga una request a las 07:00 hora de Chile:

```
GET https://<tu-app>.fly.dev/trigger-daily/<WEBHOOK_SECRET>
```

La zona horaria de Chile es `America/Santiago`. En horario de verano (septiembre-marzo) son UTC-3; en invierno UTC-4. cron-job.org permite fijar la zona horaria directamente.

## Base de datos

SQLite, creada automáticamente al arrancar. Tablas:

- **users** — `id`, `name`, `telegram_chat_id`
- **tasks** — `id`, `name`, `points`, `frequency_days`, `next_due_date`
- **assignments** — `id`, `task_id`, `user_id`, `assigned_at`, `completed_at`, `status` (`pending|completed|failed`), `points_awarded`

El archivo `.db` no se versiona (en `.gitignore`). Se regenera solo con datos de seed si no existe.

## Notas técnicas

- `core/notifications.py` llama a la API de Telegram directamente con `urllib`, sin pasar por `python-telegram-bot`. Esto permite enviar notificaciones desde fuera del contexto del bot (ej. desde un script o cron sin tener que inyectar la aplicación de Telegram).
- No hay scheduler en proceso. Las asignaciones diarias las dispara un cron externo, o localmente con `python -m apps.bots.telegram.trigger_daily`.
- `assignments` con status `pending` de días anteriores se marcan como `failed` al ejecutar la rutina diaria.
- Las tareas se asignan al usuario con menor puntaje acumulado en el mes, no aleatoriamente ni por turnos fijos.
