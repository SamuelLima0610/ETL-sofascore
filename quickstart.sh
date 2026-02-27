#!/bin/bash

# Quick Start - Guia rápido para começar

echo "========================================"
echo "  ETL Statistics API - Quick Start      "
echo "========================================"
echo ""
echo "Este guia vai te ajudar a começar rapidamente!"
echo ""

# Passo 1: Verificar ambiente virtual
echo "📦 Passo 1: Ambiente Virtual"
if [ -d "venv" ]; then
    echo "  ✅ Ambiente virtual encontrado"
    source venv/bin/activate
    echo "  ✅ Ambiente virtual ativado"
else
    echo "  ⚠️  Ambiente virtual não encontrado. Criando..."
    python3 -m venv venv
    source venv/bin/activate
    echo "  ✅ Ambiente virtual criado e ativado"
fi
echo ""

# Passo 2: Instalar dependências
echo "📚 Passo 2: Instalando dependências Python..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "  ✅ Dependências instaladas"
echo ""

# Passo 3: Verificar Redis
echo "🔴 Passo 3: Verificando Redis..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null 2>&1; then
        echo "  ✅ Redis está rodando"
    else
        echo "  ⚠️  Redis está instalado mas não está rodando"
        echo ""
        echo "  Para iniciar o Redis:"
        echo "    Ubuntu/Debian: sudo systemctl start redis"
        echo "    MacOS: brew services start redis"
        echo "    Docker: docker run -d -p 6379:6379 --name redis redis:alpine"
        echo ""
        read -p "  Deseja continuar mesmo assim? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo "  ❌ Redis não está instalado!"
    echo ""
    echo "  O Redis é necessário para o Celery funcionar."
    echo ""
    echo "  Para instalar:"
    echo "    Ubuntu/Debian: sudo apt-get install redis-server"
    echo "    MacOS: brew install redis"
    echo "    Docker: docker run -d -p 6379:6379 --name redis redis:alpine"
    echo ""
    exit 1
fi
echo ""

# Passo 4: Informações finais
echo "========================================"
echo "  ✅ Setup completo!                     "
echo "========================================"
echo ""
echo "Agora você pode iniciar os serviços:"
echo ""
echo "  ./start.sh"
echo ""
echo "Ou manualmente em terminais separados:"
echo ""
echo "  Terminal 1 (Celery Worker):"
echo "    celery -A celery_worker.celery_app worker --loglevel=info"
echo ""
echo "  Terminal 2 (API):"
echo "    python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "  Opcional - Terminal 3 (Flower - Monitoramento):"
echo "    celery -A celery_worker.celery_app flower --port=5555"
echo ""
echo "Documentação completa: README_CELERY.md"
echo ""
