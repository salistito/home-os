.PHONY: dev api web install test test-cov test-integration test-unit lint hooks

VENV := .venv/bin
FRONTEND := apps/web/frontend

dev:
	@echo "API -> http://localhost:8000  |  Front -> http://localhost:5173"
	@echo "Ctrl+C para detener ambos."
	@trap 'kill 0' EXIT INT TERM; \
	$(VENV)/python -m apps.web.api.main & \
	npm --prefix $(FRONTEND) run dev & \
	wait

api:
	$(VENV)/python -m apps.web.api.main

web:
	npm --prefix $(FRONTEND) run dev

install:
	$(VENV)/pip install -e ".[dev]"
	npm --prefix $(FRONTEND) install
	$(VENV)/python scripts/install_hooks.py

test:
	$(VENV)/pytest

test-cov:
	$(VENV)/pytest --cov=core --cov=modules --cov=apps --cov-report=term-missing --cov-fail-under=95

test-integration:
	$(VENV)/pytest -m integration

test-unit:
	$(VENV)/pytest -m unit

lint:
	$(VENV)/ruff check .

hooks:
	$(VENV)/python scripts/install_hooks.py
