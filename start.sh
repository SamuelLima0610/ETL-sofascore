#!/bin/bash

# Script para iniciar os serviços da API com Celery

echo "========================================"
echo "  ETL Statistics API - Startup Script   "
echo "========================================"
echo ""

# Ativar ambiente virtual se existir
if [ -d "venv" ]; then
    echo "✓ Ativando ambiente virtual..."
    source venv/bin/activate
else
    echo "⚠ Ambiente virtual não encontrado!"
fi

# Verificar se Redis está rodando
echo "✓ Verificando Redis..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠ Redis não está rodando!"
    echo "  Por favor, inicie o Redis primeiro:"
    echo "    - Ubuntu/Debian: sudo systemctl start redis"
    echo "    - MacOS: brew services start redis"
    echo "    - Docker: docker run -d -p 6379:6379 redis:alpine"
    exit 1
fi
echo "✓ Redis está rodando"

echo ""
echo "Iniciando serviços..."
echo ""

# Criar diretório para logs se não existir
mkdir -p logs

# Iniciar Celery Worker em background
echo "✓ Iniciando Celery Worker..."
celery -A celery_worker.celery_app worker --loglevel=info --logfile=logs/celery_worker.log &
CELERY_PID=$!
echo "  PID: $CELERY_PID"

# Aguardar um pouco para garantir que o worker iniciou
sleep 2

# Iniciar FastAPI
echo "✓ Iniciando FastAPI..."
fuser -k 8000/tcp 2>/dev/null
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!
echo "  PID: $API_PID"

echo ""
echo "========================================"
echo "  Serviços iniciados com sucesso!      "
echo "========================================"
echo ""
echo "API: http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo ""
echo "Logs:"
echo "  - Celery: logs/celery_worker.log"
echo "  - API: console"
echo ""
echo "Para parar os serviços, pressione Ctrl+C"
echo ""

# Função para parar os serviços
cleanup() {
    echo ""
    echo "Parando serviços..."
    kill $CELERY_PID 2>/dev/null
    kill $API_PID 2>/dev/null
    echo "Serviços parados."
    exit 0
}

# Capturar Ctrl+C
trap cleanup SIGINT SIGTERM

# Aguardar
wait
