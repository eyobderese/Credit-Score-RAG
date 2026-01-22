.PHONY: setup run stop clean build backend frontend ingest test

setup:
	@echo "Setting up environment..."
	python -m venv venv
	./venv/bin/pip install -r backend/requirements.txt
	cd frontend && npm install

run:
	@echo "Starting development environment..."
	make -j 2 backend frontend

backend:
	@echo "Starting backend..."
	./venv/bin/uvicorn backend.main:app --reload --port 8000

frontend:
	@echo "Starting frontend..."
	cd frontend && npm start

docker-build:
	@echo "Building Docker containers..."
	docker-compose build

docker-run:
	@echo "Starting Docker containers..."
	docker-compose up -d

docker-stop:
	@echo "Stopping Docker containers..."
	docker-compose down

ingest:
	@echo "Ingesting documents..."
	./venv/bin/python src/ingest_documents.py

test:
	@echo "Running tests..."
	./venv/bin/pytest src/ tests/

clean:
	@echo "Cleaning up..."
	rm -rf venv
	rm -rf frontend/node_modules
	rm -rf frontend/build
	find . -type d -name "__pycache__" -exec rm -rf {} +
