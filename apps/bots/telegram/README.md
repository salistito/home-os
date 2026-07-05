# Telegram bot

## Obtener el `telegram_chat_id`

Cada persona tiene un `chat_id` numérico (ej. `123456789`) que Telegram asigna a su conversación con el bot. El bot lo usa para enviarle mensajes.

Formas de obtenerlo:

- Escribirle a `@userinfobot` o `@getidsbot` en Telegram; responde con tu `chat_id`.

## Obtener el token del bot

Hablar con `@BotFather`, crear un bot con `/newbot` y copiar el token a la variable de entorno `TELEGRAM_BOT_TOKEN` (ver `.env.example`).
