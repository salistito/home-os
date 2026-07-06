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

El bot corre con webhook (no polling) cuando `WEBHOOK_URL` está definido. En la
nube se hostea como una máquina siempre encendida con un volumen para la base de
datos, así el aviso diario de las 8am siempre dispara.

`WEBHOOK_URL` es la URL pública de la app y `WEBHOOK_SECRET` valida que los
requests vengan de Telegram. `run_webhook` registra el webhook solo al arrancar,
no hay que llamar a `setWebhook` a mano.

### Setup inicial

```bash
brew install flyctl   # instalar CLI
fly auth login        # loguearse
```

### Crear y configurar la app

```bash
fly launch --no-deploy                                 # crea la app desde el fly.toml
fly volumes create homeos_data --region gru --size 1   # volumen persistente para la DB
fly secrets set \
  TELEGRAM_BOT_TOKEN=... \
  WEBHOOK_SECRET=$(openssl rand -hex 32) \
  WEBHOOK_URL=https://home-os-maristian.fly.dev \
  ANTONIA_TELEGRAM_CHAT_ID=... \
  SEBASTIAN_TELEGRAM_CHAT_ID=...
```

### Deploy

```bash
fly deploy   # construye la imagen y levanta la máquina
```

### Verificación / diagnóstico

```bash
fly logs           # ver logs (arranque, updates, errores)
fly secrets list   # ver qué secrets están cargados (nombres, no valores)
fly dashboard      # abrir el panel web (ahí está Billing)
```

### Operación / mantenimiento

```bash
fly ssh console        # entrar a la máquina (ej. borrar la DB)
fly machine restart <machine-id>   # reiniciar la máquina
```

Para recrear la base desde cero: `fly ssh console`, `rm /app/data/homeos.db`,
`exit` y reiniciar la máquina. Al arrancar se recrea el schema y se recarga el
seed.

## Contrato

API acordada entre la lógica de tareas y el bot. No se cambia sin conversarlo.

```python
def get_daily_assignments(day: date) -> list[Assignment]
def mark_task_done(text: str, user_id: str, day: date) -> MarkTaskResult
def get_month_balance(month: str) -> dict[str, int]

def notify(chat_id: str, message: str) -> None
```
