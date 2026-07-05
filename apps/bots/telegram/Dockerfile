FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV HOME_OS_DB_PATH=/app/data/homeos.db

WORKDIR /app

COPY pyproject.toml .
RUN pip install --upgrade pip && pip install hatchling

COPY . .
RUN pip install -e ".[dev]"

CMD ["python", "-m", "apps.bots.telegram.main"]
