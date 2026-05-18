.PHONY: help install dev test lint clean docker docker-up backup restore initdb

help:
	@echo "Targets:"
	@echo "  install      install Python dependencies"
	@echo "  dev          run the local Flask server"
	@echo "  test         run the unit test suite"
	@echo "  lint         run flake8"
	@echo "  initdb       create + seed the SQLite database"
	@echo "  backup       gzip the SQLite DB into ./backups/"
	@echo "  restore F=…  restore from a .db.gz file"
	@echo "  docker       build the Docker image"
	@echo "  docker-up    start docker-compose stack"
	@echo "  clean        remove .pyc/.cache/.coverage"

install:
	pip install -r requirements.txt

dev:
	bash scripts/dev.sh

test:
	py -m unittest tests.py -v

lint:
	flake8 .

initdb:
	flask --app app init-db

backup:
	bash scripts/backup.sh

restore:
	@if [ -z "$(F)" ]; then echo "Usage: make restore F=backups/file.db.gz"; exit 1; fi
	bash scripts/restore.sh $(F)

docker:
	docker build -t kcblendz:dev .

docker-up:
	docker compose up --build

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov
