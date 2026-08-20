# HomeOS

El sistema operativo de tu hogar que te ayuda a gestionar distintas áreas de la casa. Actualmente incluye los módulos de **tasks** (reparto de tareas entre integrantes), **reminders** (recordatorios personales), **finances** (finanzas del hogar por mes) y **food** (ingredientes, recetas, stock y cocina), con planes de expandirse a otras áreas.

Los canales de comunicación disponibles son **Telegram** (bot interactivo) y una **web en Vue** (visualización de datos).

> 🧑‍🤝‍🧑 HomeOS está diseñado para que cualquier persona o grupo pueda usarlo. Los usuarios se auto-registran al escribir al bot o mediante la API REST. No hay datos semilla ni configuraciones atadas a personas específicas.

## Arquitectura

El proyecto sigue una arquitectura en capas con dependencia unidireccional:

```
apps/bots/telegram/    ← entrypoint del bot (Starlette + python-telegram-bot)
apps/web/api/          ← API REST para el frontend web (tasks, reminders, finances, food)
  │
modules/tasks/         ← lógica de dominio (tareas, asignaciones, puntuación)
modules/reminders/     ← lógica de dominio (recordatorios)
modules/users/         ← lógica de dominio (usuarios, autenticación)
modules/finances/      ← lógica de dominio (finanzas del hogar)
modules/food/          ← lógica de dominio (ingredientes, recetas, stock, cocina)
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
| `schema.sql` | Esquema de la base de datos (`users`, `tasks`, `assignments`, `reminders`, `finances_*`, `food_*`) |
| `migrations/` | Migraciones DDL ejecutadas en orden por `init_db()` (ver [Database migrations](#database-migrations)) |

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
| `types.py` | Dataclass: `User`, enum `UserRole` |
| `repository.py` | Consultas SQL: create, get, update, delete, get by chat_id |
| `service.py` | Registro de usuarios con validación de duplicados |
| `errors.py` | Excepciones: `UserAlreadyExistsError`, `UserNotFoundError` |

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

### modules/food/

| Archivo | Propósito |
|---|---|
| `types.py` | Dataclasses: `Ingredient`, `IngredientMacros`, `IngredientStock`, `IngredientPurchase`, `Recipe`, `RecipeIngredient`, `RecipeMacros`, `RecipeSummary`, `CookEvent` y resultados de operación; enums: `FoodUnit`, `FoodOperationStatus`, `ExternalSource` |
| `repository.py` | Consultas SQL (ingredientes, stock, compras, recetas, recipe-ingredients, cook-events, nutrition goals) |
| `service.py` | Lógica de negocio: CRUD ingredientes/recetas, stock, compras, cocinar receta (transaccional), sugerir recetas, nutrition goals |
| `macros.py` | Cálculo de macros: `compute_recipe_macros`, `compute_cook_event_macros`, `scale_macros` |
| `suggest.py` | Algoritmos de sugerencia: `nutrition_closeness`, `stock_covers`, `variety_score` |
| `external.py` | Integración con OpenFoodFacts: búsqueda e importación de ingredientes |
| `errors.py` | Excepciones: `IngredientAlreadyExistsError`, `RecipeAlreadyExistsError`, `InsufficientStockError` |

Ver [`modules/food/README.md`](../modules/food/README.md) para el detalle de la API pública y las reglas del dominio.

### apps/bots/telegram/

| Archivo | Propósito |
|---|---|
| `main.py` | Punto de entrada: servidor Starlette + Uvicorn, rutas webhook |
| `app.py` | Construcción de la aplicación `python-telegram-bot` con handlers |
| `jobs.py` | Envío de asignaciones diarias, recordatorios del día y recordatorios con hora |
| `messages_es.py` | Mensajes de texto en español (i18n listo para agregar otros idiomas) |
| `trigger_daily.py` | Script CLI para ejecutar asignaciones diarias sin servidor web |
| `handlers/commands.py` | Comandos: `/init_home`, `/add_member`, `/join`, tasks CRUD, reminders CRUD, `/assignments`, `/balance` |
| `handlers/messages.py` | Mensajes de texto, botones inline de asignaciones y wizards de recordatorios |
| `handlers/utils/tasks.py` | Parsing de argumentos de tareas y builders de respuesta |
| `handlers/utils/reminders.py` | Parsing de argumentos de recordatorios, builders de respuesta y wizards interactivos |

### apps/web/

Frontend en Vue + Tailwind CSS para visualizar y gestionar tareas, finanzas, recordatorios y balances. La API REST está en `apps/web/api/`.

| Archivo | Propósito |
|---|---|
| `api/main.py` | Servidor Starlette + Uvicorn con rutas de la API |
| `api/middleware.py` | Middleware de autenticación JWT |
| `api/users/routes.py` | Endpoints: login, register, list, update, delete |
| `api/tasks/routes.py` | Endpoints CRUD de tareas |
| `api/tasks/scores.py` | Endpoints: ranking mensual, desglose diario, tablero del día |
| `api/reminders/routes.py` | Endpoints CRUD de recordatorios |
| `api/finances/routes.py` | Endpoints CRUD de finanzas (periodos, entradas, tags) |
| `api/food/routes.py` | Endpoints CRUD de ingredientes, stock, compras, recetas, cocinar y sugerir |
| `api/food/responses.py` | Serializadores para ingredientes, stock, compras, recetas, cook-events y errores |
| `frontend/src/` | App Vue 3 + TypeScript + Tailwind |

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
| `JWT_SECRET` | Clave secreta para firmar JWTs (generar con `openssl rand -hex 32`) |
| `WEBHOOK_URL` | URL pública del bot (para webhook) |
| `WEBHOOK_SECRET` | Token aleatorio para validar requests |
| `CRONJOB_ORG_API_KEY` | API key de cron-job.org (para recordatorios con hora) |

### Variables de entorno

| Variable | Defecto | Descripción |
|---|---|---|
| `HOME_OS_DB_PATH` | `./homeos.db` | Ruta al archivo SQLite |
| `TZ` | `America/Santiago` | Zona horaria (usada por `core.utils.get_today()`) |
| `APP_NAME` | `home-os` | Nombre de la app |
| `PORT` | `8080` | Puerto del servidor webhook |
| `WEB_PORT` | `8000` | Puerto del servidor web admin |
| `JWT_TTL_DAYS` | `365` | Días de validez de los JWTs |
| `WEB_ALLOWED_ORIGINS` | `""` | Orígenes CORS permitidos (separados por coma) |
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
python -m scripts.trigger_daily
```

Esto inicializa la base de datos, ejecuta el mismo algoritmo de asignación que usa el cron en producción y envía los mensajes por Telegram a cada integrante.

### Verificar instalación

```bash
python -c "import core, modules.tasks, modules.reminders, modules.users, modules.finances, modules.food, apps.bots.telegram; print('imports OK')"
```

### Linter

```bash
ruff check .
```

Ruff usa `line-length = 100`. El frontend tiene typecheck con `vue-tsc --noEmit`:

```bash
cd apps/web/frontend && npm run typecheck
```

## Testing

Framework: **pytest** con `unittest.mock`. Configuración en `pyproject.toml` (`[tool.pytest.ini_options]`).

### Ejecutar tests

```bash
pytest                        # todos los tests
pytest -m unit                # solo unitarios (dependencias mockeadas)
pytest -m integration         # solo integración (SQLite real)
pytest -x                     # parar en el primer fallo
make test                     # alias de pytest
make test-unit                # alias de pytest -m unit
make test-integration         # alias de pytest -m integration
```

### Cobertura

```bash
pytest --cov=core --cov=modules --cov=apps --cov-report=term-missing --cov-fail-under=95
pytest --cov=core --cov=modules --cov=apps --cov-report=html
make test-cov                 # alias del primer comando (core + modules + apps, falla si < 95%)
```

### Pre-push hook

Ejecuta `ruff check` + `pytest --cov-fail-under=95` antes de cada push:

```bash
make hooks                        # Linux/Mac
python scripts/install_hooks.py   # Windows
```

Para saltarlo en un push puntual:

```bash
git push --no-verify
```

El hook está en `.git/hooks/pre-push`. Se elimina con `rm .git/hooks/pre-push` (Linux/Mac) o `del .git\hooks\pre-push` (Windows).

### Comandos equivalentes (PowerShell / Windows)

| `make ...` | PowerShell |
|---|---|
| `make test` | `.venv\Scripts\python -m pytest` |
| `make test-cov` | `.venv\Scripts\python -m pytest --cov=core --cov=modules --cov=apps --cov-fail-under=95` |
| `make test-unit` | `.venv\Scripts\python -m pytest -m unit` |
| `make test-integration` | `.venv\Scripts\python -m pytest -m integration` |
| `make lint` | `.venv\Scripts\python -m ruff check .` |
| `make hooks` | `.venv\Scripts\python scripts/install_hooks.py` |

### Estructura

```
tests/
├── conftest.py               # fixtures compartidas (db, db_user, frozen_now, jwt_secret)
├── core/                     # unitarios para core/utils y core/db
├── modules/                  # integración (repository) + unitarios (service)
│   ├── users/
│   ├── tasks/
│   ├── reminders/
│   ├── finances/
│   └── food/
└── apps/                     # unitarios para handlers de Telegram y rutas de la API
    ├── bots/telegram/
    └── web/api/
```

### Estrategia

- **Repository** (`@pytest.mark.integration`): SQLite real en directorio temporal. El fixture `db` en `conftest.py` redirige `HOME_OS_DB_PATH` a un archivo temporal y ejecuta `init_db()`.
- **Service** (`@pytest.mark.unit`): mockea el módulo `repository` importado por el servicio con `@patch`. Sin DB real.
- **API routes**: mockea los servicios/repositorios; llama a las funciones handler directamente con `Request` mockeados.
- **Telegram handlers**: mockea `Update`, `ContextTypes` y los servicios/repositorios.

## Usuarios

No hay datos semilla ni usuarios predefinidos. El primer usuario en registrarse se convierte en **administrador** del hogar. A partir de ahí, solo el administrador puede crear nuevos usuarios.

Los usuarios se eliminan de forma lógica (soft-delete). Un usuario eliminado:
- No puede iniciar sesión.
- No puede recibir nuevas tareas.
- No se le pueden asignar entradas ni recordatorios.
- Sigue apareciendo en el historial (balances, rankings, finanzas).

El último administrador no puede ser eliminado.

### Inicializar el hogar (primer usuario, admin)

El primer usuario debe inicializar el hogar por cualquiera de estas vías:

#### 1. Comando `/init_home` en el bot de Telegram

```text
/init_home Juan Pérez
```

Crea al primer usuario del hogar con rol de administrador y vincula su chat de Telegram.

#### 2. API REST (pública, sin token)

```bash
curl -X POST https://rpi.your-tailnet.ts.net/api/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Juan", "password": "secreto"}'
```

> Si creas el primer usuario por API REST, luego debes ejecutar `/join <tu_nombre>` en Telegram para vincular tu chat y poder usar el bot.

### Agregar integrantes (solo admin)

Una vez inicializado el hogar, el admin puede agregar integrantes:

#### Comando `/add_member` (admin en Telegram)

```text
/add_member María
```

El nuevo integrante debe vincular su cuenta de Telegram ejecutando:

```text
/join María
```

#### API REST (requiere token del admin)

```bash
curl -X POST https://rpi.your-tailnet.ts.net/api/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token_del_admin>" \
  -d '{"name": "María", "password": "secreto"}'
```

## Módulo de Tasks

### Uso del bot de Telegram

| Comando / Acción | Descripción |
|---|---|
| `/start` | Mensaje de bienvenida con instrucciones |
| `/help` | Muestra la ayuda (alias de /start) |
| `/init_home <name>` | Inicializa el hogar y crea al administrador |
| `/add_member <name>` | Agrega un nuevo integrante (solo admin) |
| `/join <name>` | Vincula tu cuenta de Telegram a tu usuario |
| `/tasks` | Explicación de los comandos CRUD de tareas |
| `/add_task <name> <points> [freq]` | Crea una tarea nueva |
| `/list_tasks` | Lista todas las tareas con formato tabla |
| `/edit_task <name> <field> <value>` | Edita nombre, puntos o frecuencia de una tarea |
| `/delete_task <name>` | Elimina una tarea (borra sus asignaciones pendientes) |
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

Frontend en Vue para visualizar tareas, finanzas, recordatorios y balances. Incluye API REST (`apps/web/api/`) con endpoints para users CRUD, tasks CRUD, reminders CRUD, ranking mensual, desglose diario, tablero del día y finances CRUD.

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

1. El cron diario (07:00) ejecuta `/trigger_daily_assignments/{token}` para generar asignaciones del día.
2. El cron diario también ejecuta `/trigger_day_reminders/{token}` para enviar recordatorios sin hora específica.
3. Un cron frecuente (cada 5-15 min) ejecuta `/trigger_timed_reminders/{token}` para recordatorios con hora específica.
4. Los recordatorios con hora crean un one-shot job en [cron-job.org](https://cron-job.org) al crearse, y se actualizan o eliminan al editarlos/borrarlos.
5. Al enviar un recordatorio recurrente, se crea el próximo con `trigger_at` + intervalo.

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

## Modulo de Food

Modulo solo-web (sin comandos de Telegram) para gestionar ingredientes, stock, compras, recetas y cocinar.

### Conceptos

- **Ingrediente**: un alimento del catalogo con nombre, categoria, unidad (`FoodUnit`), macros nutricionales por porcion y opcionalmente `purchase_unit`/`purchase_conversion_factor` para operaciones de stock/compra en unidades alternativas.
- **Stock**: inventario por ingrediente con `quantity` actual, `min_alert_quantity` para alertas de stock bajo, y `expiration_date` opcional.
- **Compra**: registro de compra que incrementa automaticamente el stock. Incluye `price` (entero, currency-agnostic) y `purchased_at`. Se puede revertir si el stock no se ha consumido.
- **Receta**: plato global del hogar con nombre, categoria, porciones, pasos e ingredientes. Los macros de la receta se computan, no se persisten.
- **Cocinar**: acepta `user_id` y un `ingredients` opcional para sobreescribir cantidades/unidades. Es transaccional: si falta stock, rollback y se devuelven los ingredientes faltantes. Los macros del evento se computan y persisten.
- **Recomendador**: filtra recetas factibles por stock, opcionalmente orientado a objetivos nutricionales (`GoalTarget` o metas guardadas del usuario), con soporte para variedad (excluye recetas cocinadas recientemente).
- **Objetivos nutricionales**: metas diarias por usuario (kcal, proteinas, carbohidratos, grasas) que el recomendador usa para rankear sugerencias.
- **Fuentes externas**: busqueda e importacion de ingredientes desde OpenFoodFacts.

### Web (Vue + API REST)

Endpoints (`apps/web/api/food/`):

| Metodo | Ruta | Descripcion |
|---|---|---|
| `POST` | `/api/food/ingredients` | Crea un ingrediente |
| `GET` | `/api/food/ingredients` | Lista ingredientes (filtro `?category=`) |
| `GET` | `/api/food/ingredients/{id}` | Obtiene un ingrediente |
| `PATCH` | `/api/food/ingredients/{id}` | Actualiza un ingrediente |
| `DELETE` | `/api/food/ingredients/{id}` | Soft-delete de ingrediente |
| `POST` | `/api/food/ingredients/search` | Busca ingrediente en fuente externa (OpenFoodFacts) |
| `POST` | `/api/food/ingredients/import` | Importa ingrediente desde fuente externa |
| `GET` | `/api/food/stock` | Lista el stock |
| `GET` | `/api/food/stock/low` | Stock bajo el umbral |
| `GET` | `/api/food/stock/expiring` | Stock por vencer (`?days=`) |
| `PATCH` | `/api/food/stock/{ingredient_id}` | Actualiza stock de un ingrediente |
| `POST` | `/api/food/purchases` | Registra una compra |
| `GET` | `/api/food/purchases` | Lista compras (filtros `?ingredient_id=&from_date=&to_date=`) |
| `DELETE` | `/api/food/purchases/{id}` | Elimina una compra y revierte stock |
| `POST` | `/api/food/recipes` | Crea una receta |
| `GET` | `/api/food/recipes` | Lista recetas (filtro `?ingredient_ids=`) |
| `GET` | `/api/food/recipes/suggested` | Sugiere recetas factibles (`?limit=&only_with_stock=&category=&goal_target=...&variety_days=`) |
| `GET` | `/api/food/recipes/{id}` | Obtiene una receta con ingredientes resueltos |
| `PATCH` | `/api/food/recipes/{id}` | Actualiza una receta |
| `DELETE` | `/api/food/recipes/{id}` | Soft-delete de receta |
| `POST` | `/api/food/recipes/{id}/cook` | Cocina una receta (body: `{portions, ingredients?, cooked_at?}`) |
| `GET` | `/api/food/cook-events` | Lista eventos de cocina (filtros `?recipe_id=&user_id=&from_date=&to_date=`) |
| `GET` | `/api/food/goals` | Obtiene objetivos nutricionales del usuario autenticado |
| `PATCH` | `/api/food/goals` | Actualiza objetivos nutricionales del usuario |

## Contrato de la API

### Users (`modules/users/repository.py`)

```python
def create_user(user_name: str, role: str = "member") -> User

def get_users() -> list[User]

def get_active_users() -> list[User]

def get_active_user_by_id(user_id: int) -> User | None

def get_active_user_by_name(user_name: str) -> User | None

def get_active_user_by_telegram_chat_id(telegram_chat_id: str) -> User | None

def update_user(user_id: int, **fields: str | int | None) -> bool

def delete_user(user_id: int) -> bool
```

Service layer:

```python
def create_user(user_name: str, role: str = "member", password: str | None = None, telegram_chat_id: str | None = None) -> User
```

### Tasks (`modules/tasks/service.py`)

La interfaz entre la lógica de dominio y las apps. No se cambia sin conversarlo.

```python
def create_task(task_name: str, points: int, frequency_days: int | None = None, next_due_date: str | None = None) -> TaskOperationResult

def update_active_task(task_id: int, **kwargs: str | int | None) -> TaskOperationResult

def soft_delete_active_task(task_id: int) -> TaskOperationResult

def get_daily_assignments(day: date) -> list[Assignment] # Si no hay asignaciones para el día, las genera automáticamente

def get_pending_daily_assignments(day: date) -> list[Assignment]

def mark_assignment_done(text: str, user_id: int, day: date) -> AssignmentCompletionResult

def fail_stale_pending_assignments(day: date) -> int

def get_month_points(month: str) -> dict[int, int]

def get_daily_points(month: str) -> dict[str, dict[int, int]]

def get_daily_task_breakdown(month: str) -> dict[str, dict[int, list[dict]]]

def get_day_board(day: date) -> dict[int, list[dict]]
```

### Reminders (`modules/reminders/service.py`)

```python
def create_reminder(user_id: int, message: str, trigger_at: str, trigger_time: str | None, recurrence: str) -> ReminderOperationResult

def get_user_reminders(user_id: int) -> list[Reminder]

def get_user_pending_reminders(user_id: int) -> list[Reminder]

def get_due_day_reminders() -> list[Reminder]

def get_due_timed_reminders() -> list[Reminder]

def advance_recurrence(reminder: Reminder) -> Reminder | None

def update_reminder(reminder_id: int, user_id: int, **kwargs: str | None) -> ReminderOperationResult

def delete_reminder(reminder_id: int, user_id: int) -> ReminderOperationResult

def delete_reminder_by_message(user_id: int, message: str) -> ReminderOperationResult

def process_reminder_states(reminders: list[Reminder]) -> None
```

### Finances (`modules/finances/service.py`)

```python
def open_period(label: str | None = None) -> PeriodOperationResult

def get_periods() -> list[Period]

def get_period_detail(period_id: int) -> PeriodDetailResult

def add_entry(period_id: int, kind: str, scope: str, owner_id: int, label: str, amount: int | None, tags: list[str] | None = None) -> EntryOperationResult

def update_entry(entry_id: int, *, label: str | None = None, owner_id: int | None = None, amount: int | None = None, detail_mode: str | None = None, details: list[tuple[str, int]] | None = None, tags: list[str] | None = None) -> EntryOperationResult

def delete_entry(entry_id: int) -> EntryOperationResult

def confirm_entry(entry_id: int) -> EntryOperationResult

def list_entries(period_id: int) -> list[Entry]

def list_tags() -> list[Tag]
```

### Food (`modules/food/service.py`)

```python
def create_ingredient(name: str, category: str | None, unit: str, macros: dict, purchase_unit: str | None = None, purchase_conversion_factor: float | None = None, external_source: str | None = None, external_id: str | None = None) -> FoodOperationResult

def update_ingredient(ingredient_id: int, name: str | None = None, category: str | None = None, unit: str | None = None, macros: dict | None = None, purchase_unit: str | None = None, purchase_conversion_factor: float | None = None) -> FoodOperationResult

def delete_ingredient(ingredient_id: int) -> FoodOperationResult

def get_ingredient(ingredient_id: int) -> FoodOperationResult

def list_ingredients(category: str | None = None) -> list[Ingredient]

def search_ingredient_from_external(name: str, source: str = "openfoodfacts") -> list[dict]

def import_ingredient_from_external(name: str, source: str = "openfoodfacts") -> FoodOperationResult

def set_stock(ingredient_id: int, quantity: float, unit: str | None = None, min_alert_quantity: float = 0.0, expiration_date: str | None = None) -> FoodOperationResult

def get_stock() -> list[IngredientStock]

def get_low_stock() -> list[IngredientStock]

def get_expiring_soon(days: int = 7) -> list[IngredientStock]

def register_purchase(ingredient_id: int, quantity: float, price: int, purchased_at: str, unit: str | None = None, notes: str | None = None) -> FoodOperationResult

def list_purchases(ingredient_id: int | None = None, from_date: str | None = None, to_date: str | None = None) -> list[IngredientPurchase]

def delete_purchase(purchase_id: int) -> FoodOperationResult

def create_recipe(name: str, portions: int, ingredients: list[dict], category: str | None = None, description: str | None = None, steps: list[str] | None = None) -> FoodOperationResult

def update_recipe(recipe_id: int, name: str | None = None, category: str | None = None, portions: int | None = None, description: str | None = None, steps: list[str] | None = None, ingredients: list[dict] | None = None) -> FoodOperationResult

def delete_recipe(recipe_id: int) -> FoodOperationResult

def get_recipe(recipe_id: int) -> FoodOperationResult

def list_recipes(ingredient_ids: list[int] | None = None) -> list[Recipe]

def cook_recipe(recipe_id: int, user_id: int, portions_cooked: int, ingredients: list[dict] | None = None, cooked_at: str | None = None) -> CookResult

def compute_recipe_macros(recipe: Recipe) -> RecipeMacros

def list_cook_events(recipe_id: int | None = None, user_id: int | None = None, from_date: str | None = None, to_date: str | None = None) -> list[CookEvent]

def suggest_recipes(user_id: int | None = None, category: str | None = None, limit: int = 3, only_with_stock: bool = True, goal_target: GoalTarget | None = None, variety_days: int = 0) -> SuggestResult

def get_nutrition_goals(user_id: int) -> FoodOperationResult

def update_nutrition_goals(user_id: int, kcal_target: int | None = None, protein_g_target: float | None = None, carbs_g_target: float | None = None, fat_g_target: float | None = None) -> FoodOperationResult
```

## Docker

```bash
cp .env.example .env
# completa TELEGRAM_BOT_TOKEN y JWT_SECRET como mínimo
docker compose up --build
```

La base de datos persiste en `./data` gracias al volumen definido en `docker-compose.yml`.

## Producción

HomeOS corre en modo webhook sobre Starlette + Uvicorn. El despliegue recomendado es un servidor casero (p. ej. Raspberry Pi 5) con Docker Compose.

### Rutas expuestas

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/telegram` | Recibe updates de Telegram (validado con header `X-Telegram-Bot-Api-Secret-Token`). |
| `GET`/`POST` | `/trigger_daily_assignments/{token}` | Genera y envía las asignaciones diarias. `token` = `WEBHOOK_SECRET`. |
| `GET`/`POST` | `/trigger_day_reminders/{token}` | Envía recordatorios del día sin hora específica. |
| `GET`/`POST` | `/trigger_timed_reminders/{token}` | Envía recordatorios con hora específica. |

### Requisitos

- Servidor Linux 64-bit (Raspberry Pi OS 64-bit recomendado) con Docker y Docker Compose.
- Una forma de exponer el servidor a Internet (Telegram exige HTTPS en el webhook).
- Un bot de Telegram (`TELEGRAM_BOT_TOKEN`).
- Acceso SSH si se usa deploy automático.

### 1. Preparar el servidor

```bash
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

### 2. Exponer el servidor a Internet

**Opción A — Tailscale Funnel** (sin IP pública ni dominio):

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
sudo tailscale serve --bg 8080
sudo tailscale funnel --bg 8080
```

La URL pública queda como `https://<maquina>.<tailnet>.ts.net`.

**Opción B — Cloudflare Tunnel** (requiere dominio propio):

```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o cloudflared
sudo install cloudflared /usr/local/bin/
cloudflared tunnel login
cloudflared tunnel create homeos
```

**Opción C — Dominio propio + reverse proxy** (requiere IP pública o DDNS): apunta el dominio al servidor y usa Caddy/Nginx para terminar TLS y reenviar al puerto `8080`.

### 3. Variables de entorno

Crear `.env` en la raíz del repo:

```bash
TZ=America/Santiago
HOME_OS_DB_PATH=/app/data/homeos.db
TELEGRAM_BOT_TOKEN=<token>
WEBHOOK_URL=https://<url-publica>
WEBHOOK_SECRET=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
PORT=8080
WEB_ALLOWED_ORIGINS=https://<frontend>.vercel.app
```

### 4. Levantar Docker Compose

```bash
git clone <repo-url> home-os
cd home-os
mkdir -p data
# copia el .env y, si aplica, la DB a data/homeos.db
docker compose up --build -d
```

Verificar:

```bash
docker logs -f homeos
curl https://<url-publica>/api/health   # {"status":"ok"}
```

El bot configura el webhook de Telegram automáticamente al arrancar si `WEBHOOK_URL` y `WEBHOOK_SECRET` están seteados. El contenedor se llama `homeos`.

### 5. Cron

**Opción A — cron externo (cron-job.org):**

| Endpoint | Frecuencia |
|---|---|
| `GET https://<url-publica>/trigger_daily_assignments/<WEBHOOK_SECRET>` | 1/día (07:00) |
| `GET https://<url-publica>/trigger_day_reminders/<WEBHOOK_SECRET>` | 1/día (07:05) |
| `GET https://<url-publica>/trigger_timed_reminders/<WEBHOOK_SECRET>` | Cada 10 min |

**Opción B — cron local en el servidor:**

```cron
0 7 * * * curl -s http://localhost:8080/trigger_daily_assignments/<WEBHOOK_SECRET>
5 7 * * * curl -s http://localhost:8080/trigger_day_reminders/<WEBHOOK_SECRET>
*/10 * * * * curl -s http://localhost:8080/trigger_timed_reminders/<WEBHOOK_SECRET>
```

La zona horaria es `America/Santiago` (configurable con `TZ`).

### 6. Frontend

El frontend (`apps/web/frontend/`) se publica por separado (Vercel u otro static host). Configurar:

- `VITE_API_URL=https://<url-publica>` en el build del frontend.
- `WEB_ALLOWED_ORIGINS` en el backend con el dominio del frontend (CORS).

### 7. Deploy automático con GitHub Actions

El workflow `.github/workflows/deploy-rpi.yml` se dispara tras pasar CI en `main`. Primero conecta el runner a Tailscale vía OAuth y luego hace SSH al servidor para ejecutar `git reset --hard origin/main` + `docker compose up --build -d`.

Prerequisito: la Raspberry Pi debe estar en la misma tailnet y tener el repo en `~/apps/home-os`.

Secrets del repositorio:

| Secret | Descripción |
|---|---|
| `RPI_HOST` | Hostname de Tailscale del servidor (ej. `raspberrypi5.<tailnet>.ts.net`). |
| `RPI_USER` | Usuario SSH. |
| `RPI_SSH_KEY` | Clave privada SSH (la pública en `~/.ssh/authorized_keys`). |
| `TS_OAUTH_CLIENT_ID` | OAuth client ID de Tailscale para el runner de CI. |
| `TS_OAUTH_SECRET` | OAuth client secret de Tailscale. |

### Troubleshooting

| Síntoma | Causa probable | Solución |
|---|---|---|
| El bot no responde | El webhook apunta a otra URL | Verificar con `curl "https://api.telegram.org/bot<token>/getWebhookInfo"` y `docker compose restart` |
| Today board vacío | Las asignaciones no se generaron | `docker exec homeos sh -c 'python -m scripts.trigger_daily'` |
| Los mensajes de Telegram llegan pero el today board está vacío | El webhook apunta a otra instancia (p. ej. un host anterior) | Verificar `getWebhookInfo` y reiniciar el contenedor para reconfigurar el webhook |
| Bot en modo polling | `WEBHOOK_URL`/`WEBHOOK_SECRET` no seteados | Revisar `.env` y `docker compose restart` |
| Deploy falla | SSH/secret incorrecto | Verificar secrets y `~/.ssh/authorized_keys` |

## Base de datos

SQLite, creada automáticamente al arrancar. Tablas:

- **users** — `id`, `name`, `role`, `password_hash`, `telegram_chat_id`, `deleted_at`
- **tasks** — `id`, `name`, `points`, `frequency_days`, `next_due_date`, `deleted_at` (soft delete)
- **assignments** — `id`, `task_id`, `user_id`, `assigned_at`, `completed_at`, `status` (`pending|completed|failed`), `points_awarded`, `source` (`task|cooking`), `source_entity_id`, `source_entity_details`
- **reminders** — `id`, `user_id`, `message`, `trigger_at`, `trigger_time`, `recurrence` (`none|daily|weekly|monthly|yearly`), `cron_job_id`, `created_at`, `owner` (`user|system`), `system_ref_entity`, `system_ref_entity_id`
- **finances_periods** — `id`, `label`, `status` (`open|closed`), `opened_at`
- **finances_entries** — `id`, `period_id`, `kind` (`income|expense`), `scope` (`shared|personal`), `owner_id`, `label`, `amount` (nullable), `status` (`pending|confirmed`), `paid_at`, `detail_mode` (`none|top_down|bottom_up`), `created_at`
- **finances_entry_details** — `id`, `entry_id`, `label`, `amount`
- **finances_tags** — `id`, `name` (único, case-insensitive), `color`, `created_at`
- **finances_entry_tags** — `entry_id`, `tag_id` (tabla de union, PK compuesta)
- **food_ingredients** — `id`, `name`, `category`, `unit`, `macros` (JSON), `purchase_unit`, `purchase_conversion_factor`, `external_source`, `external_id`, `created_at`, `updated_at`, `deleted_at`
- **food_stock** — `id`, `ingredient_id`, `quantity`, `min_alert_quantity`, `expiration_date`, `updated_at`
- **food_purchases** — `id`, `ingredient_id`, `quantity`, `price`, `purchased_at`, `notes`, `created_at`
- **food_recipes** — `id`, `name`, `category`, `description`, `portions`, `steps` (JSON), `created_at`, `updated_at`, `deleted_at`
- **food_recipe_ingredients** — `id`, `recipe_id`, `ingredient_id`, `quantity`, `unit`
- **food_cook_events** — `id`, `recipe_id`, `user_id`, `portions`, `macros` (JSON), `cooked_at`, `created_at`
- **food_cook_event_ingredients** — `id`, `cook_event_id`, `ingredient_id`, `ingredient_name`, `quantity`, `unit`, `macros` (JSON)
- **food_nutrition_goals** — `id`, `user_id`, `kcal_target`, `protein_g_target`, `carbs_g_target`, `fat_g_target`, `updated_at`

Índices únicos:
- `idx_active_tasks_unique_name` — un nombre activo por tarea (`WHERE deleted_at IS NULL`)
- `idx_one_pending_assignment_per_task` — una asignación pendiente por tarea
- `idx_one_completed_task_assignment_per_day` — una asignación completada por tarea por día (`source = 'task'`)
- `idx_one_completed_cooking_assignment_per_event` — una asignación de cocina completada por evento (`source = 'cooking'`)
- `idx_one_open_period` — un solo periodo de finanzas `open` a la vez (`WHERE status = 'open'`)

Índices:
- `idx_reminders_pending_due` — recordatorios por fecha para búsqueda eficiente
- `idx_finances_entries_period` — entradas por periodo
- `idx_finances_entry_details_entry` — detalles por entrada
- `idx_finances_entry_tags_tag` — relación tag→entradas

El archivo `.db` no se versiona (en `.gitignore`).

## Backup de la base de datos (producción)

La DB de producción vive en la Raspberry Pi en `~/apps/home-os/data/homeos.db`.

### Backup manual

```bash
cp ~/apps/home-os/data/homeos.db ~/backups/homeos-$(date +%Y%m%d).db
```

### Rotación de backups

```bash
find ~/backups -name 'homeos-*.db' -mtime +7 -delete
```

### Inspeccionar la DB local

```bash
python scripts/private/inspect_db.py data/homeos.db
```

Muestra tablas, conteo de filas y las primeras 25 filas de cada tabla.

### Notas

- La DB en `data/` está en `.gitignore` y no se versiona.
- Los scripts de utilidad están en `scripts/private/` (también en `.gitignore`).

## Notas técnicas

- No hay scheduler en proceso. Las asignaciones diarias y recordatorios los dispara un cron externo, o localmente con `python -m scripts.trigger_daily`.
- Los recordatorios con hora específica usan [cron-job.org](https://cron-job.org) para programar notificaciones push precisas (one-shot jobs vía REST API).
- `assignments` con status `pending` de días anteriores se marcan como `failed` al ejecutar la rutina diaria.
- Las tareas se asignan al usuario con menor puntaje acumulado en el mes, no aleatoriamente ni por turnos fijos.
- Los recordatorios recurrentes se auto-generan al dispararse (next trigger = current + interval).
- Las fechas se calculan en zona horaria `America/Santiago` (no UTC).
