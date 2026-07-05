FROM python:3.12-slim

WORKDIR /app

# Install build tooling and dependencies
COPY pyproject.toml .
RUN pip install --upgrade pip && pip install hatchling

# Copy project
COPY . .

# Install editable (dev extras optional)
RUN pip install -e ".[dev]"

CMD ["python", "-m", "modules.tasks"]
