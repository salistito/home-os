# HomeOS

El sistema operativo de tu hogar. Gestiona tareas, finanzas y recordatorios desde Telegram o desde el panel web.

HomeOS está pensado para familias, roommates o cualquier grupo que conviva: cada persona se registra al hablarle al bot, las tareas se reparten solas cada mañana según los puntos acumulados del mes, y las finanzas se llevan mes a mes con gastos compartidos o personales.

---

## ¿Qué puedes hacer?

🧹 **Tareas con sistema de puntos**
Crea tareas recurrentes (ej. "Lavar la loza cada 2 días") u ocasionales ("Sacar la basura"). Cada tarea da puntos. HomeOS las asigna automáticamente cada mañana al integrante con menos puntos acumulados, manteniendo el equilibrio sin que nadie tenga que decidir quién hace qué.

📊 **Ranking y tablero diario**
Consulta el balance mensual con el ranking de puntos de cada integrante. El panel web incluye un desglose día a día y un tablero con las tareas pendientes de hoy.

🔔 **Recordatorios personales**
Programa alertas con tiempo relativo (`en 3h`, `en 2d`), fecha exacta (`2026-12-07`) o con hora (`2026-07-20 14:30`). Pueden ser de una sola vez o recurrentes (`daily`, `weekly`, `monthly`, `yearly`). Las notificaciones llegan por Telegram a la hora indicada.

💰 **Finanzas del hogar**
Lleva los gastos e ingresos mes a mes. Cada mes es un periodo: al abrir uno nuevo se cierra el anterior y se copian las entradas confirmadas. Las entradas pueden ser compartidas o personales, con tags de colores y desglose por integrante.

🌐 **Multi-canal**
Todo se puede hacer desde el bot de Telegram o desde el panel web (Vue + Tailwind). El panel web es responsive y se ve bien en el celular.

---

## Requisitos

- **Python 3.12** o superior
- Un **bot de Telegram** (lo creas gratis con [@BotFather](https://t.me/BotFather) en 2 minutos)
- Una cuenta en [Fly.io](https://fly.io) si quieres hostearlo (tienen tier gratuito; el costo estimado es ~USD 0.15/mes por el volumen de 1 GB)

---

## Instalación local

Clona el repo, crea un entorno virtual e instala las dependencias:

```bash
git clone <repo>
cd home-os
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Copia el archivo de variables de entorno y edítalo:

```bash
cp .env.example .env
```

Abre `.env` y completa al menos estas dos variables:

```
TELEGRAM_BOT_TOKEN=el_token_que_te_dio_botfather
JWT_SECRET=una_clave_secreta_larga_y_aleatoria
```

> Para generar un `JWT_SECRET` seguro: `python -c "import secrets; print(secrets.token_hex(32))"`.

Eso es todo. No hay seeds, usuarios predefinidos ni configuraciones adicionales.

---

## Ejecución local

```bash
python -m apps.bots.telegram.main
```

El bot arranca en **modo polling** (escucha actualizaciones de Telegram sin necesidad de un servidor público). También levanta la API y el panel web en `http://localhost:8000`.

Si quieres probar la asignación diaria de tareas sin esperar al cron ni configurar webhooks, ejecuta:

```bash
python -m apps.bots.telegram.trigger_daily
```

Esto ejecuta la misma rutina que corre en producción y envía las tareas del día por Telegram a cada integrante.

### Verificar que todo funciona

```bash
python -c "import core, modules.tasks, modules.reminders, modules.users, modules.finances, apps.bots.telegram; print('imports OK')"
```

---

## Primeros pasos

### 1. Inicializa tu hogar

Háblale a tu bot en Telegram:

```
/init_home TuNombre
```

Eres el primer usuario y automáticamente eres el **administrador**. Solo tú puedes agregar nuevos miembros.

### 2. Agrega integrantes

```
/add_member María
```

Cada nuevo integrante debe vincular su cuenta de Telegram al usuario que creaste:

```
/join María
```

> Si María no tiene Telegram a mano, también puedes registrar usuarios desde el panel web o la API REST. Luego ella podrá vincular su chat con `/join` cuando quiera.

### 3. Crea tareas

```
/add_task Lavar la loza 4 2
```

Esto crea una tarea recurrente que da **4 puntos** y se repite **cada 2 días**. HomeOS la asignará automáticamente cada mañana.

Una tarea ocasional (sin frecuencia fija):

```
/add_task Sacar la basura 1
```

### 4. Consulta tus tareas y el ranking

```
/assignments
/balance
```

---

## Comandos del bot

### Hogar

| Comando | Descripción |
|---|---|
| `/start` | Mensaje de bienvenida con todos los comandos |
| `/help` | Igual que `/start` |
| `/init_home <nombre>` | Inicializa el hogar (solo la primera vez, sin usuarios) |
| `/add_member <nombre>` | Agrega un nuevo integrante (solo admin) |
| `/join <nombre>` | Vincula tu chat de Telegram a tu usuario |

### Tareas

| Comando | Descripción |
|---|---|
| `/tasks` | Explicación de comandos y tipos de tareas |
| `/add_task <nombre> <puntos> [frecuencia] [fecha]` | Crea una tarea nueva |
| `/list_tasks` | Lista todas las tareas del hogar |
| `/edit_task <nombre> <campo> <valor>` | Edita una tarea por nombre |
| `/delete_task <nombre>` | Elimina una tarea |
| `/assignments` | Tus tareas de hoy con botones para marcarlas hechas |
| `/balance` | Ranking de puntos acumulados del mes |

**Ejemplos de `/add_task`:**

```
/add_task Barrer la cocina 2 3               → recurrente, cada 3 días, 2 pts
/add_task Sacar la basura 1                    → ocasional, sin frecuencia, 1 pt
/add_task Limpiar ventanas 5 30 2026-08-01    → recurrente, cada 30 días, empieza el 1 de agosto
```

**Ejemplos de `/edit_task`:**

```
/edit_task Barrer name Barrer el living       → cambia el nombre
/edit_task Lavar la loza points 6             → cambia los puntos
/edit_task Lavar la loza freq 7               → cambia la frecuencia a 7 días
/edit_task Lavar la loza next_occurrence 2026-08-01 → cambia la próxima ocurrencia
```

### Recordatorios

| Comando | Descripción |
|---|---|
| `/reminders` | Explicación de comandos y tipos de recordatorios |
| `/add_reminder <mensaje> <tiempo> [recurrencia]` | Crea un recordatorio |
| `/list_reminders` | Lista tus recordatorios activos |
| `/edit_reminder <mensaje> <campo> <valor>` | Edita un recordatorio |
| `/delete_reminder <mensaje>` | Elimina un recordatorio |

Los comandos `/add_reminder`, `/edit_reminder` y `/delete_reminder` también funcionan sin argumentos: el bot te guía paso a paso con un wizard interactivo.

**Formatos de tiempo:**

| Formato | Ejemplo | Significado |
|---|---|---|
| Relativo | `3h` | En 3 horas |
| Relativo | `1h30m` | En 1 hora y 30 minutos |
| Relativo | `2d` | En 2 días |
| Relativo | `1w` | En 1 semana |
| Absoluto | `2026-07-20` | El 20 de julio de 2026 (todo el día) |
| Absoluto con hora | `2026-07-20 14:30` | El 20 de julio a las 14:30 |

**Recurrencias disponibles:** `none` (por defecto), `daily`, `weekly`, `monthly`, `yearly`.

**Ejemplos de `/add_reminder`:**

```
/add_reminder Colgar la ropa 3h                         → en 3 horas, una vez
/add_reminder Comprar regalo 2026-12-07                 → el 7 de diciembre
/add_reminder Tomar vitaminas 2026-07-14 09:00 daily    → todos los días a las 09:00
/add_reminder Cumpleaños mamá 2026-11-14 yearly         → cada año el 14 de noviembre
```

**Ejemplos de `/edit_reminder`:**

```
/edit_reminder Cumpleaños mamá message Cumple mamá      → cambia el mensaje
/edit_reminder Cumple mamá trigger_at 2026-12-07        → cambia la fecha
/edit_reminder Reunión trigger_time 15:00               → cambia la hora
/edit_reminder Cumple mamá recurrence yearly            → la hace recurrente anual
```

---

## Panel web

Además del bot, tienes un panel web completo en `http://localhost:8000` (o en `https://<tu-app>.fly.dev` en producción).

### Iniciar sesión por primera vez

Los usuarios creados desde Telegram **no tienen contraseña** hasta que se las asignas. Para ponerle contraseña a un usuario:

```bash
python scripts/set_password.py <user_id>
```

El `<user_id>` lo puedes ver inspeccionando la base de datos o desde el panel de administración de usuarios (solo admin).

Una vez con contraseña, entra a la web, inicia sesión con tu nombre y contraseña, y listo.

### Módulos del panel

🧹 **Tareas**
- Tabla con todas las tareas del hogar (crear, editar, eliminar).
- Widget de ranking mensual con los puntos acumulados de cada integrante.
- Desglose diario: cuántos puntos ganó cada persona cada día del mes.
- Tablero de hoy: qué tareas están pendientes para cada integrante.

💰 **Finanzas**
- Selector de periodos (meses). Al abrir uno nuevo, el anterior se cierra automáticamente y sus entradas confirmadas se copian al nuevo mes.
- Entradas de ingreso o gasto, compartidas (`shared`) o personales (`personal`).
- Tags de colores para categorizar (ej. "supermercado", "luz", "sueldo").
- Dos vistas: **Compartido** (gastos compartidos y resumen de contribuciones por persona) y **Persona** (ingresos y gastos de cada integrante).
- Las entradas pueden crearse sin monto (`pending`) y confirmarse después.

🔔 **Recordatorios**
- Tabla con todos tus recordatorios activos (crear, editar, eliminar).
- Muestra fecha, hora, recurrencia y mensaje.

---

## Lleva tu HomeOS a producción en Fly.io

Fly.io es un PaaS que permite correr aplicaciones en múltiples regiones. HomeOS aprovecha que las máquinas se apagan solas sin tráfico y solo pagas por el volumen (USD ~0.15/mes). Cuando llega un request entrante, la máquina arranca automáticamente.

### 1. Prepara tu bot de Telegram

1. Abre Telegram y busca [@BotFather](https://t.me/BotFather).
2. Envía `/newbot` y sigue las instrucciones (ponle nombre y usuario).
3. Guarda el **token** que te da. Es algo como `123456:ABC-DEF1234gh...`.

### 2. Instala Fly.io CLI

Sigue la guía oficial según tu sistema operativo: https://fly.io/docs/hands-on/install-flyctl/

Luego inicia sesión:

```bash
fly auth signup   # o fly auth login si ya tienes cuenta
```

### 3. Clona el repo y configura

```bash
git clone <repo>
cd home-os
```

### 4. Lanza la app en Fly.io

```bash
fly launch --no-deploy
```

Elige un nombre para tu app (ej. `mi-casa`), la región `gru` (Santiago), y responde **No** cuando pregunte si quieres deployar ahora. Esto crea el archivo `fly.toml`.

### 5. Crea el volumen para la base de datos

```bash
fly volumes create homeos_data --region gru --size 1
```

El volumen persiste la base de datos SQLite entre deploys y reinicios.

### 6. Configura las variables secretas

Necesitas cuatro secrets. La URL debe coincidir con el nombre que elegiste:

```bash
fly secrets set \
  TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234gh..." \
  JWT_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')" \
  WEBHOOK_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')" \
  WEBHOOK_URL="https://mi-casa.fly.dev"
```

> En Git Bash o Linux/macOS usa `$(openssl rand -hex 32)` en vez del comando de Python. El resultado es el mismo.

### 7. Deploya

```bash
fly deploy
```

Cuando termine, ve a `https://<tu-app>.fly.dev/api/health`. Deberías ver `{"status":"ok"}`.

### 8. Verifica el webhook de Telegram

HomeOS configura el webhook automáticamente al arrancar si las variables `WEBHOOK_URL` y `WEBHOOK_SECRET` están presentes. Abre tu bot en Telegram y envía `/start`. Si responde, está funcionando.

Si no responde, revisa los logs:

```bash
fly logs
```

### 9. Configura el cron externo

HomeOS no tiene scheduler propio. Necesitas un cron externo que llame a los endpoints de triggers. Recomendamos [cron-job.org](https://cron-job.org) (gratuito).

Crea una cuenta y agrega los siguientes cron jobs apuntando a tu app. Reemplaza `<WEBHOOK_SECRET>` por el valor que generaste en el paso 6.

| Endpoint | Frecuencia | Descripción |
|---|---|---|
| `GET https://<tu-app>.fly.dev/trigger-daily/<WEBHOOK_SECRET>` | 1 vez al día (ej. 07:00) | Asigna tareas y envía los mensajes de la mañana a cada integrante |
| `GET https://<tu-app>.fly.dev/trigger-day-reminders/<WEBHOOK_SECRET>` | 1 vez al día (ej. 07:05) | Envía recordatorios del día sin hora específica |
| `GET https://<tu-app>.fly.dev/trigger-timed-reminders/<WEBHOOK_SECRET>` | Cada 10 minutos | Envía recordatorios con hora exacta |

> La zona horaria de Chile es `America/Santiago`. En cron-job.org puedes elegir `Chile Standard Time` en la configuración de zona horaria de cada job.

### 10. Accede al panel web

El panel web está disponible en `https://<tu-app>.fly.dev`. ¡No olvides ponerle contraseña a los usuarios con `scripts/set_password.py`! Para eso puedes conectarte a la máquina:

```bash
fly ssh console
python scripts/set_password.py <user_id>
```

---

## Docker (alternativa local)

Si prefieres usar Docker sin instalar Python:

```bash
cp .env.example .env
# edita .env con TELEGRAM_BOT_TOKEN y JWT_SECRET
docker compose up --build
```

La base de datos persiste en la carpeta `./data`. Por defecto corre en modo polling; si configuras `WEBHOOK_URL` y `WEBHOOK_SECRET` en el `.env` se activa el modo webhook.

---

## Notas útiles

- **Zona horaria**: `America/Santiago` por defecto (configurable con la variable `TZ`).
- **Primer usuario**: el primero que ejecuta `/init_home` es el **admin**. Los siguientes son `member`.
- **Soft-delete**: los usuarios no se borran físicamente, se desactivan. Siguen apareciendo en el historial pero no pueden recibir nuevas tareas ni iniciar sesión. El último admin no se puede eliminar.
- **Recordatorios con hora**: usan la API de cron-job.org para programar notificaciones precisas. Solo necesitas configurar la variable `CRONJOB_ORG_API_KEY` en el `.env` si usas recordatorios con hora. Sin esta variable los recordatorios con hora se envían solo cuando el cron de `trigger-timed-reminders` los detecta como pendientes.
- **Asignación por puntos**: las tareas se asignan al integrante con **menor puntaje acumulado** en el mes. Si hay empate, se elige al azar. Si un integrante ya alcanzó su tope diario (`1.5 × la tarea con más puntos`), no recibe más tareas ese día.

---

## Documentación técnica

La documentación completa para desarrolladores está en [`docs/README.md`](docs/README.md): arquitectura por capas, contrato de la API, esquema de base de datos, migraciones y más.
