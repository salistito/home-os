# HomeOS

El sistema operativo de tu hogar que te ayuda a gestionar distintas áreas de la casa. Actualmente incluye los módulos de **tasks** (reparto de tareas entre integrantes), **reminders** (recordatorios personales) y **finances** (finanzas del hogar por mes), con planes de expandirse a otras áreas (cocina, inventario, etc.).

Los canales de comunicación disponibles son **Telegram** (bot interactivo) y una **web en Vue** (visualización de datos).

## Arquitectura

El proyecto sigue una arquitectura en capas con dependencia unidireccional:

```
apps/bots/telegram/    ← entrypoint del bot (Starlette + python-telegram-bot)
apps/web/api/          ← API REST para el frontend web (tasks, reminders, finances)
  │
modules/tasks/         ← lógica de dominio (tareas, asignaciones, puntuación)
modules/reminders/     ← lógica de dominio (recordatorios)
modules/users/         ← lógica de dominio (usuarios, autenticación)
modules/finances/      ← lógica de dominio (finanzas del hogar)
  │
core/                  ← infraestructura compartida (config, DB, schema, utils)
```

Reglas de dependencia:
- `core/` **no puede** importar de `modules/` ni `apps/`.
- `modules/` puede importar solo de `core/`.
- `apps/` puede importar de ambos.

### core/

| Archivo | Propósito |
|---|---|
| `config.py` | Carga variables de entorno desde `.env` usando `python-dotenv` |
| `utils/date.py` | Utilidades de fecha: `get_today()`, `format_date()`, `to_db_date()`, `next_due_date()`, `month_key()`, arrays `DAYS` y `MONTHS` |
| `utils/string.py` | Utilidades de texto: `normalize_string()`, `html_escape()` |
| `db.py` | Conexión SQLite con `row_factory = sqlite3.Row` y `PRAGMA foreign_keys = ON` |
| `schema.sql` | Esquema de la base de datos (`users`, `tasks`, `assignments`, `reminders`, `finances_*`) |
| `seed.py` | Carga datos iniciales desde archivos YAML en `seed/` |

### modules/tasks/

| Archivo | Propósito |
|---|---|
| `types.py` | Dataclasses: `Task`, `Assignment`, `TaskOperationResult`, `AssignmentCompletionResult` and enums: `TaskOperationStatus`, `AssignmentCompletionStatus` |
| `repository.py` | Consultas SQL (tasks, assignments, puntos por usuario) |
| `service.py` | Lógica de negocio: asignar tareas, marcar como hechas, balance mensual |
| `errors.py` | Excepciones: `TaskAlreadyExistsError`, `TaskNotFoundError` |

### modules/users/

| Archivo | Propósito |
|---|---|
| `types.py` | Dataclass: `User` |
| `repository.py` | Consultas SQL: get user by id, by chat_id, get password hash |

### modules/reminders/

| Archivo | Propósito |
|---|---|
| `types.py` | Dataclasses: `Reminder`, `ReminderOperationResult` and enums: `ReminderRecurrence`, `ReminderOperationStatus` |
| `repository.py` | Consultas SQL (CRUD de recordatorios, query de pendientes, cron_job_id) |
| `service.py` | Lógica de negocio: crear, editar, cancelar, procesar recordatorios due, avanzar recurrencia |
| `cron.py` | Integración con cron-job.org REST API: crear, actualizar y eliminar one-shot jobs para recordatorios con hora |
| `errors.py` | Excepciones: `ReminderAlreadyExistsError`, `ReminderNotFoundError` |

### modules/finances/

| Archivo | Propósito |
|---|---|
| `types.py` | Dataclasses: `Period`, `Entry`, `EntryDetail`, `Tag`, `PersonSummary`, `PeriodSummary`, `PeriodDetail` y resultados de operación; enums: `PeriodStatus`, `EntryKind`, `EntryScope`, `EntryStatus`, `DetailMode`, `FinanceOperationStatus` |
| `repository.py` | Consultas SQL (periodos, entradas, detalles, tags y sus relaciones) |
| `service.py` | Lógica de negocio: abrir periodos, agregar/editar/confirmar entradas, resumen por persona |
| `errors.py` | Excepción: `OpenPeriodExistsError` |

Ver [`modules/finances/README.md`](modules/finances/README.md) para el detalle de la API pública y las reglas del dominio.

### apps/bots/telegram/

| Archivo | Propósito |
|---|---|
| `main.py` | Punto de entrada: servidor Starlette + Uvicorn, rutas webhook |
| `app.py` | Construcción de la aplicación `python-telegram-bot` con handlers |
| `jobs.py` | Envío de asignaciones diarias, recordatorios del día y recordatorios con hora |
| `messages_es.py` | Mensajes de texto en español (i18n listo para agregar otros idiomas) |
| `trigger_daily.py` | Script CLI para ejecutar asignaciones diarias sin servidor web |
| `handlers/commands.py` | Comandos: tasks CRUD, reminders CRUD, `/assignments`, `/balance` |
| `handlers/messages.py` | Mensajes de texto, botones inline de asignaciones y wizards de recordatorios |
| `handlers/utils/tasks.py` | Parsing de argumentos de tareas y builders de respuesta |
| `handlers/utils/reminders.py` | Parsing de argumentos de recordatorios, builders de respuesta y wizards interactivos |

### apps/web/

Frontend en Vue para visualizar datos de tareas, asignaciones y balances.

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
| `CRONJOB_ORG_API_KEY` | API key de cron-job.org (para recordatorios con hora) |

> Para obtener tu `chat_id`, envía un mensaje a [@userinfobot](https://t.me/userinfobot) en Telegram.

### Variables de entorno

| Variable | Defecto | Descripción |
|---|---|---|
| `HOME_OS_DB_PATH` | `./homeos.db` | Ruta al archivo SQLite |
| `TZ` | `America/Santiago` | Zona horaria (usada por `core.utils.get_today()`) |
| `PORT` | `8080` | Puerto del servidor webhook |
| `WEB_PORT` | `8000` | Puerto del servidor web admin |
| `CRONJOB_ORG_API_KEY` | `""` | API key de cron-job.org para recordatorios con hora |

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
python -c "import core, modules.tasks, modules.reminders, modules.users, modules.finances, apps.bots.telegram; print('imports OK')"
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

- **Recurrente** (con `frequency_days`): se asigna automáticamente cada N días.
- **Ocasional** (sin `frequency_days`): los integrantes la marcan como hecha cuando quieran.

Para tareas recurrentes, el `next_due_date` se puede definir de dos formas:

- `start_offset_days`: se calcula como `hoy + offset`.
- `next_due_date`: fecha exacta en formato `YYYY-MM-DD` (tiene prioridad sobre `start_offset_days`).

```yaml
tasks:
  - name: Lavar la loza
    points: 3
    frequency_days: 2
    next_due_date: "2026-07-13"
  - name: Regar las plantas
    points: 2
    frequency_days: 7
    start_offset_days: 1
  - name: Sacar el reciclaje
    points: 2
```

Las tareas se cargan una sola vez al crear la DB. Si la tabla `tasks` ya tiene datos, el seed se salta.

### `seed/assignments.yaml`

Define asignaciones históricas para poblar la DB (útil para migrar datos o reiniciar). Usa `task_name` y `user_name` para referenciar por nombre (se resuelven a IDs automáticamente).

```yaml
assignments:
  - task_name: Lavar la loza
    user_name: Sebastián
    assigned_at: "2026-07-06"
    status: completed
    completed_at: "2026-07-06"
    points_awarded: 6

  - task_name: Regar las plantas
    user_name: Antonia
    assigned_at: "2026-07-06"
    status: completed
    completed_at: "2026-07-06"
    points_awarded: 2

  - task_name: Lavar la loza
    user_name: Sebastián
    assigned_at: "2026-07-08"
    status: failed
```

Las asignaciones se cargan una sola vez. Si la tabla `assignments` ya tiene datos, el seed se salta.

## Módulo de Tasks

### Uso del bot de Telegram

| Comando / Acción | Descripción |
|---|---|
| `/start` | Mensaje de bienvenida con instrucciones |
| `/help` | Muestra la ayuda (alias de /start) |
| `/tasks` | Explicación de los comandos CRUD de tareas |
| `/add_task <name> <points> [freq]` | Crea una tarea nueva |
| `/list_tasks` | Lista todas las tareas con formato tabla |
| `/edit_task <name> <field> <value>` | Edita nombre, puntos o frecuencia de una tarea |
| `/delete_task <name>` | Elimina una tarea (solo si no tiene asignaciones pendientes) |
| `/assignments` | Muestra las tareas pendientes de hoy con botones |
| `/balance` | Muestra los puntos acumulados este mes |
| `Escribir nombre de tarea` | Marca una tarea como completada (coincidencia exacta, case-insensitive) |
| Botón inline | Marca la tarea como completada desde el mensaje de la mañana |
| `/reminders` | Explicación de comandos de recordatorios |
| `/add_reminder` | Crea un recordatorio (wizard o args inline) |
| `/list_reminders` | Lista tus recordatorios |
| `/edit_reminder` | Edita un recordatorio (wizard o args inline) |
| `/delete_reminder` | Elimina un recordatorio (wizard o args inline) |

### ¿Cómo funciona la asignación diaria?

1. Se marcan como `failed` las tareas pendientes de días anteriores.
2. Se buscan tareas recurrentes cuya `next_due_date` sea hoy o anterior, ordenadas por puntos de mayor a menor.
3. Se asignan al integrante con **menos puntos acumulados en el mes actual**. En caso de empate, se elige al azar.
4. Cada integrante tiene un **tope diario de puntos** igual a `1.5 × la tarea con más puntos del día`. Al alcanzarlo, no recibe más tareas ese día. Las tareas que nadie puede tomar se saltan y quedan pendientes para el próximo ciclo.
5. Se envía un mensaje a cada integrante con sus tareas y botones para marcar como hecha.
6. Al marcar como hecha, se recalcula `next_due_date = today + frequency_days`.

### Web (Vue + API REST)

Frontend en Vue para visualizar datos de tasks, asignaciones y balances. Incluye API REST (`apps/web/api/`) con endpoints para tasks CRUD, reminders CRUD, ranking mensual, desglose diario y tablero del día.

## Módulo de Reminders

### Uso del bot de Telegram

| Comando / Acción | Descripción |
|---|---|
| `/reminders` | Explicación de los comandos CRUD de recordatorios |
| `/add_reminder <msg> <tiempo> [recurrencia]` | Crea recordatorio. Ej: `/add_reminder Sacar la ropa 3h` |
| `/add_reminder <msg> <fecha> [recurrencia]` | Crea recordatorio con fecha. Ej: `/add_reminder Cumpleaños mamá 2026-07-20 yearly` |
| `/add_reminder <msg> <fecha> <hora> [recurrencia]` | Fecha + hora. Ej: `/add_reminder Reunión 2026-07-20 14:30` |
| `/add_reminder` | Inicia wizard interactivo (bot pregunta mensaje, tiempo y recurrencia) |
| `/list_reminders` | Lista recordatorios pendientes del usuario |
| `/edit_reminder <msg> <campo> <valor>` | Edita un recordatorio (`message`, `trigger_at`, `trigger_time`, `recurrence`) |
| `/edit_reminder` | Inicia wizard interactivo para editar |
| `/delete_reminder <msg>` | Elimina un recordatorio por mensaje |
| `/delete_reminder` | Inicia wizard interactivo para eliminar |

### Formatos de tiempo

**Relativo** (desde ahora):
- `3h` = 3 horas
- `30m` = 30 minutos
- `1h30m` = 1 hora 30 minutos
- `2d` = 2 días
- `1w` = 1 semana

**Absoluto**:
- `2026-07-20` = solo fecha (全天)
- `2026-07-20 14:30` = fecha + hora exacta

### Recurrencia

Los recordatorios pueden ser de una sola vez o recurrentes:

| Recurrencia | Descripción |
|---|---|
| `none` | Una vez (por defecto) |
| `daily` | Se repite diariamente |
| `weekly` | Se repite semanalmente |
| `monthly` | Se repite mensualmente |
| `yearly` | Se repite anualmente (ej: cumpleaños) |

Al dispararse un recordatorio recurrente, se crea automáticamente el siguiente con la fecha calculada.

### ¿Cómo funciona el scheduling?

1. El cron diario (07:00) ejecuta `/trigger-daily/{token}` para generar asignaciones del día.
2. El cron diario también ejecuta `/trigger-day-reminders/{token}` para enviar recordatorios sin hora específica.
3. Un cron frecuente (cada 5-15 min) ejecuta `/trigger-timed-reminders/{token}` para recordatorios con hora específica.
4. Los recordatorios con hora crean un one-shot job en [cron-job.org](https://cron-job.org) al crearse, y se actualizan o eliminan al editarlos/borrarlos.
5. Al enviar un recordatorio recurrente, se crea el próximo con `trigger_at` + intervalo.
6. Si la máquina está parada, el próximo request la arranca y procesa recordatorios pendientes.

## Módulo de Finanzas

Módulo solo-web (sin comandos de Telegram) para llevar las finanzas del hogar mes a mes. Cada mes es un **periodo**, y dentro de él se registran **entradas** de ingreso o gasto, compartidas o personales, con tags de colores.

### Conceptos

- **Periodo**: un mes de presupuesto. Solo puede haber uno `open` a la vez. Al abrir uno nuevo se cierra el anterior y se clonan sus entradas confirmadas al nuevo mes.
- **Entrada**: un ingreso o gasto. Puede crearse sin monto (queda `pending`) y confirmarse después; confirmar requiere un monto. Los ingresos deben ser personales.
- **Scope**: `shared` (compartido) o `personal`. Solo los gastos compartidos suman al total compartido y a las contribuciones por persona.
- **Detalle**: una entrada puede desglosarse en ítems. En modo `bottom_up` el monto se calcula sumando los detalles.
- **Tags**: etiquetas con color, deduplicadas sin distinguir mayúsculas y con máximo 30 caracteres.

### Web (Vue + API REST)

Frontend en Vue para gestionar periodos y entradas. Endpoints (`apps/web/api/finances/`):

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/finances/periods` | Abre un periodo (cierra el anterior y clona sus entradas confirmadas) |
| `GET` | `/api/finances/periods` | Lista los periodos |
| `GET` | `/api/finances/periods/{id}` | Detalle de un periodo con entradas y resumen |
| `GET` | `/api/finances/tags` | Lista los tags |
| `POST` | `/api/finances/entries` | Crea una entrada |
| `GET` | `/api/finances/entries?period_id=` | Lista las entradas de un periodo |
| `PATCH` | `/api/finances/entries/{id}` | Edita una entrada |
| `DELETE` | `/api/finances/entries/{id}` | Elimina una entrada |
| `POST` | `/api/finances/entries/{id}/confirm` | Confirma una entrada pendiente |

## Contrato de la API

### Users (`modules/users/repository.py`)

```python
def get_users() -> list[User]

def get_user_by_id(user_id: str) -> User | None

def get_user_by_chat_id(chat_id: str) -> User | None

def get_password_hash(user_id: str) -> str | None
```

### Tasks (`modules/tasks/service.py`)

La interfaz entre la lógica de dominio y las apps. No se cambia sin conversarlo.

```python
def create_task(task_name: str, points: int, frequency_days: int | None = None, next_due_date: str | None = None) -> TaskOperationResult

def update_active_task(task_id: int, **kwargs: str | int | None) -> TaskOperationResult

def soft_delete_active_task(task_id: int) -> TaskOperationResult

def get_daily_assignments(day: date) -> list[Assignment] # Si no hay asignaciones para el día, las genera automáticamente

def get_pending_daily_assignments(day: date) -> list[Assignment]

def mark_assignment_done(text: str, user_id: str, day: date) -> AssignmentCompletionResult

def fail_stale_pending_assignments(day: date) -> int

def get_month_points(month: str) -> dict[str, int]

def get_daily_points(month: str) -> dict[str, dict[str, int]]

def get_daily_task_breakdown(month: str) -> dict[str, dict[str, list[dict]]]

def get_day_board(day: date) -> dict[str, list[dict]]
```

### Reminders (`modules/reminders/service.py`)

```python
def create_reminder(user_id: str, message: str, trigger_at: str, trigger_time: str | None, recurrence: str) -> ReminderOperationResult

def get_user_reminders(user_id: str) -> list[Reminder]

def get_user_pending_reminders(user_id: str) -> list[Reminder]

def get_due_day_reminders() -> list[Reminder]

def get_due_timed_reminders() -> list[Reminder]

def advance_recurrence(reminder: Reminder) -> Reminder | None

def update_reminder(reminder_id: int, user_id: str, **kwargs: str | None) -> ReminderOperationResult

def delete_reminder(reminder_id: int, user_id: str) -> ReminderOperationResult

def delete_reminder_by_message(user_id: str, message: str) -> ReminderOperationResult
```

### Finances (`modules/finances/service.py`)

```python
def open_period(label: str | None = None) -> PeriodOperationResult

def get_periods() -> list[Period]

def get_period_detail(period_id: int) -> PeriodDetailResult

def add_entry(period_id: int, kind: str, scope: str, owner_id: str, label: str, amount: int | None, tags: list[str] | None = None) -> EntryOperationResult

def update_entry(entry_id: int, *, label: str | None = None, owner_id: str | None = None, amount: int | None = None, detail_mode: str | None = None, details: list[tuple[str, int]] | None = None, tags: list[str] | None = None) -> EntryOperationResult

def delete_entry(entry_id: int) -> EntryOperationResult

def confirm_entry(entry_id: int) -> EntryOperationResult

def list_entries(period_id: int) -> list[Entry]

def list_tags() -> list[Tag]
```

## Docker

```bash
cp .env.example .env
# completa TELEGRAM_BOT_TOKEN y los chat IDs
docker compose up --build
```

La base de datos persiste en `./data` gracias al volumen definido en `docker-compose.yml`.

## Producción (Fly.io)

El bot corre en modo webhook sobre Starlette + Uvicorn con cuatro rutas:

- `POST /telegram` — recibe updates de Telegram (validado con header `X-Telegram-Bot-Api-Secret-Token`).
- `GET|POST /trigger-daily/<WEBHOOK_SECRET>` — dispara asignaciones diarias. Lo llama un cron externo 1 vez al día.
- `GET|POST /trigger-day-reminders/<WEBHOOK_SECRET>` — envía recordatorios del día sin hora específica. Lo llama un cron externo 1 vez al día.
- `GET|POST /trigger-timed-reminders/<WEBHOOK_SECRET>` — envía recordatorios con hora específica. Lo llama un cron externo cada 5-15 min.

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
- **tasks** — `id`, `name`, `points`, `frequency_days`, `next_due_date`, `deleted_at` (soft delete)
- **assignments** — `id`, `task_id`, `user_id`, `assigned_at`, `completed_at`, `status` (`pending|completed|failed`), `points_awarded`
- **reminders** — `id`, `user_id`, `message`, `trigger_at`, `trigger_time`, `recurrence` (`none|daily|weekly|monthly|yearly`), `cron_job_id`, `created_at`
- **finances_periods** — `id`, `label`, `status` (`open|closed`), `opened_at`
- **finances_entries** — `id`, `period_id`, `kind` (`income|expense`), `scope` (`shared|personal`), `owner_id`, `label`, `amount` (nullable), `status` (`pending|confirmed`), `paid_at`, `detail_mode` (`none|top_down|bottom_up`), `created_at`
- **finances_entry_details** — `id`, `entry_id`, `label`, `amount`
- **finances_tags** — `id`, `name` (único, case-insensitive), `color`, `created_at`
- **finances_entry_tags** — `entry_id`, `tag_id` (tabla de unión, PK compuesta)

Índices únicos:
- `idx_tasks_unique_active_name` — un nombre activo por tarea (`WHERE deleted_at IS NULL`)
- `idx_assignment_one_pending_per_task` — una asignación pendiente por tarea
- `idx_assignment_one_completed_per_day` — una asignación completada por tarea por día
- `idx_one_open_period` — un solo periodo de finanzas `open` a la vez (`WHERE status = 'open'`)

Índices:
- `idx_reminders_pending_due` — recordatorios por fecha para búsqueda eficiente
- `idx_finances_entries_period` — entradas por periodo
- `idx_finances_entry_details_entry` — detalles por entrada
- `idx_finances_entry_tags_tag` — relación tag→entradas

El archivo `.db` no se versiona (en `.gitignore`). Se regenera solo con datos de seed si no existe.

## Backup de la base de datos (producción)

La DB de producción vive en un volumen de Fly.io (`/app/data/homeos.db`). Para descargar una copia local:

### Opción 1: Script automático (PowerShell)

```powershell
.\scripts\private\backup_db.ps1
```

Esto:
1. Inicia la máquina si está detenida
2. Descarga la DB a `data/homeos_<timestamp>.db` y `data/homeos.db`
3. Verifica la integridad de la copia
4. Detiene la máquina para ahorrar costos

Para especificar otro directorio de salida:

```powershell
.\scripts\private\backup_db.ps1 -OutputDir "backups"
```

### Opción 2: Comandos manuales

```bash
# Verificar estado
fly status

# Si la máquina está detenida, iniciarla
fly machine start <machine_id>

# Descargar la DB
fly ssh sftp get /app/data/homeos.db data/homeos.db

# Detener la máquina después del backup
fly machine stop <machine_id>
```

### Inspeccionar la DB de producción directamente

Sin descargar la DB, ejecuta `inspect_db.py` directamente en el servidor de Fly.io:

```bash
python scripts/private/inspect_prod_db.py
```

Esto:
1. Inicia la máquina si está detenida
2. Sube el script de inspección a `/tmp/inspect.py` en el servidor
3. Lo ejecuta contra la DB de producción
4. Muestra tablas, conteo de filas y las primeras 25 filas de cada tabla

### Inspeccionar la DB local

```bash
python scripts/private/inspect_db.py data/homeos.db
```

Muestra tablas, conteo de filas y las primeras 25 filas de cada tabla.

### Notas

- La DB en `data/` está en `.gitignore` y no se versiona.
- Ambos scripts (`backup_db.ps1` e `inspect_prod_db.py`) auto-inician la máquina si está detenida y la detienen después de operar.
- Los scripts están en `scripts/private/` (también en `.gitignore`).

## Notas técnicas

- No hay scheduler en proceso. Las asignaciones diarias y recordatorios los dispara un cron externo, o localmente con `python -m apps.bots.telegram.trigger_daily`.
- Los recordatorios con hora específica usan [cron-job.org](https://cron-job.org) para programar notificaciones push precisas (one-shot jobs vía REST API).
- `assignments` con status `pending` de días anteriores se marcan como `failed` al ejecutar la rutina diaria.
- Las tareas se asignan al usuario con menor puntaje acumulado en el mes, no aleatoriamente ni por turnos fijos.
- Los recordatorios recurrentes se auto-generan al dispararse (next trigger = current + interval).
- Las fechas se calculan en zona horaria `America/Santiago` (no UTC).
