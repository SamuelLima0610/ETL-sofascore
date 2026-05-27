#!/usr/bin/env bash
# Script para rodar testes
# Usage: ./run_tests.sh [option]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if venv is activated
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo -e "${YELLOW}⚠️  Virtual environment not activated${NC}"
    echo "Run: source venv/bin/activate"
    exit 1
fi

# Install test dependencies if needed
if ! python -c "import pytest" 2>/dev/null; then
    echo -e "${YELLOW}📦 Installing test dependencies...${NC}"
    pip install -q -r requirements-dev.txt
fi

echo -e "${GREEN}🧪 Running tests...${NC}\n"

case "${1:-all}" in
    all)
        echo "Running all tests with coverage..."
        pytest tests/ --cov=. --cov-report=html --cov-report=term
        echo -e "${GREEN}✅ All tests passed!${NC}"
        echo "Coverage report: htmlcov/index.html"
        ;;
    unit)
        echo "Running unit tests only..."
        pytest tests/ -m "not integration" -v
        ;;
    integration)
        echo "Running integration tests only..."
        pytest tests/ -m "integration" -v
        ;;
    fast)
        echo "Running tests without coverage (fast mode)..."
        pytest tests/ -v
        ;;
    watch)
        echo "Running tests in watch mode..."
        if ! python -c "import pytest_watch" 2>/dev/null; then
            echo -e "${YELLOW}⚠️  pytest-watch not found. Installing...${NC}"
            pip install -q pytest-watch
        fi
        pytest-watch tests/ -- -v
        ;;
    coverage)
        echo "Running tests with coverage report..."
        pytest tests/ --cov=. --cov-report=html --cov-report=term
        echo "Opening coverage report..."
        open htmlcov/index.html || xdg-open htmlcov/index.html || echo "Coverage report: htmlcov/index.html"
        ;;
    parallel)
        echo "Running tests in parallel..."
        if ! python -c "import xdist" 2>/dev/null; then
            echo -e "${YELLOW}⚠️  pytest-xdist not found. Installing...${NC}"
            pip install -q pytest-xdist
        fi
        pytest tests/ -n auto -v
        ;;
    file)
        if [[ -z "${2}" ]]; then
            echo -e "${RED}❌ Please specify a test file${NC}"
            echo "Usage: ./run_tests.sh file test_file_name.py"
            exit 1
        fi
        echo "Running tests from ${2}..."
        pytest "tests/${2}" -v
        ;;
    *)
        echo -e "${RED}❌ Unknown option: ${1}${NC}"
        echo "Available options:"
        echo "  all          - Run all tests with coverage (default)"
        echo "  unit         - Run unit tests only"
        echo "  integration  - Run integration tests only"
        echo "  fast         - Run tests without coverage"
        echo "  watch        - Run tests in watch mode (requires pytest-watch)"
        echo "  coverage     - Run tests with coverage and open report"
        echo "  parallel     - Run tests in parallel (requires pytest-xdist)"
        echo "  file <name>  - Run specific test file"
        exit 1
        ;;
esac
