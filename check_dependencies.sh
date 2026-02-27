#!/bin/bash

# Script para verificar dependências

echo "========================================"
echo "  Verificação de Dependências          "
echo "========================================"
echo ""

# Python
echo -n "Python: "
if command -v python3 &> /dev/null; then
    python3 --version
else
    echo "❌ Não encontrado"
fi

# Pip
echo -n "Pip: "
if command -v pip &> /dev/null; then
    pip --version | head -n 1
else
    echo "❌ Não encontrado"
fi

# Redis
echo -n "Redis: "
if command -v redis-server &> /dev/null; then
    redis-server --version
    echo -n "  Status: "
    if redis-cli ping &> /dev/null; then
        echo "✅ Rodando"
    else
        echo "⚠️  Instalado mas não está rodando"
        echo "  Para iniciar:"
        echo "    - Ubuntu/Debian: sudo systemctl start redis"
        echo "    - MacOS: brew services start redis"
        echo "    - Docker: docker run -d -p 6379:6379 redis:alpine"
    fi
else
    echo "❌ Não instalado"
    echo "  Para instalar:"
    echo "    - Ubuntu/Debian: sudo apt-get install redis-server"
    echo "    - MacOS: brew install redis"
    echo "    - Docker: docker run -d -p 6379:6379 redis:alpine"
fi

echo ""

# Verificar pacotes Python
echo "Pacotes Python:"
PACKAGES=("fastapi" "uvicorn" "celery" "redis" "requests" "beautifulsoup4" "pymongo")
for pkg in "${PACKAGES[@]}"; do
    echo -n "  $pkg: "
    if python3 -c "import $pkg" 2>/dev/null; then
        version=$(python3 -c "import $pkg; print($pkg.__version__)" 2>/dev/null)
        echo "✅ $version"
    else
        echo "❌ Não instalado"
    fi
done

echo ""
echo "========================================"
