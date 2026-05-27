#!/usr/bin/env bash
# Quick Start - Testes do ETL Statistics API
# Este script roda os testes e mostra um resumo

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        ETL Statistics API - Test Suite Quick Start             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if venv exists
if [[ ! -d "venv" ]]; then
    echo "❌ Virtual environment not found. Create it first:"
    echo "   python -m venv venv"
    exit 1
fi

# Activate venv
source venv/bin/activate

echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "📦 Installing test dependencies..."
pip install -q -r requirements-dev.txt 2>/dev/null || pip install -r requirements-dev.txt
echo "✅ Dependencies installed"
echo ""

# Run tests
echo "🧪 Running test suite..."
echo ""

pytest tests/ -v --tb=short

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ Test Suite Complete                      ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║ 📊 For more options:                                           ║"
echo "║    • Run coverage:     pytest tests/ --cov=. --cov-report=html║"
echo "║    • Run in parallel:  pytest tests/ -n auto                  ║"
echo "║    • See all commands: make help (ou ./run_tests.sh)          ║"
echo "║                                                                ║"
echo "║ 📖 Read more: tests/TESTS_README.md                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
