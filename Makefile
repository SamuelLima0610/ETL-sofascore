# Makefile para desenvolvimento e testes

.PHONY: help install install-dev test test-unit test-integration test-coverage lint format clean

help:
	@echo "Available commands:"
	@echo "  make install          - Install dependencies"
	@echo "  make install-dev      - Install development dependencies"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-coverage    - Run tests with coverage report"
	@echo "  make lint             - Run linting (flake8)"
	@echo "  make format           - Format code with black"
	@echo "  make clean            - Remove cache and build artifacts"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v

test-unit:
	pytest tests/ -v -m "not integration"

test-integration:
	pytest tests/ -v -m "integration"

test-coverage:
	pytest tests/ --cov=. --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated: htmlcov/index.html"

test-fast:
	pytest tests/ -v --tb=short

lint:
	flake8 . --exclude=venv,__pycache__,.pytest_cache --max-line-length=120
	pylint --disable=all --enable=E,F routers/ etl/ utils/ schemas/

format:
	black . --exclude=venv

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name htmlcov -exec rm -rf {} +
	find . -type f -name .coverage -delete
	find . -type f -name "*.pyc" -delete

.DEFAULT_GOAL := help
