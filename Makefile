.PHONY: test dev-api dev-web mcp-stdio up down up-mcp

test:
	cd backend && python -m pytest -q

dev-api:
	cd backend && uvicorn main:app --reload --port 8000

dev-web:
	cd frontend && npm run dev

mcp-stdio:
	cd backend && python mcp_server.py

up:
	docker compose up --build -d

up-mcp:
	docker compose --profile mcp up --build -d

down:
	docker compose down
