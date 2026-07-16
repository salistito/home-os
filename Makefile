.PHONY: dev api web install

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
