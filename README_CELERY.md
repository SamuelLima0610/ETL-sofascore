# ETL Statistics API com Celery

API para extração de estatísticas de futebol do SofaScore com processamento em background usando Celery.

## 🚀 Funcionalidades

- ✅ Extração de dados de jogos do Brasileirão Série A
- ✅ Processamento em background para requisições longas
- ✅ Monitoramento de progresso de tasks
- ✅ Transformação de dados opcional
- ✅ API REST com documentação automática

## 📋 Pré-requisitos

- Python 3.8+
- Redis (broker para Celery)

### Instalação do Redis

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

**MacOS:**
```bash
brew install redis
brew services start redis
```

**Docker:**
```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

## 🔧 Instalação

1. Clone o repositório e entre no diretório:
```bash
cd etl-statistics
```

2. Crie e ative o ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

## 🏃 Executando

### Opção 1: Script Automático (Linux/Mac)

```bash
chmod +x start.sh
./start.sh
```

### Opção 2: Manual

**Terminal 1 - Celery Worker:**
```bash
celery -A celery_worker.celery_app worker --loglevel=info
```

**Terminal 2 - API:**
```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

### Opção 3: Celery com Flower (Monitoramento Web)

```bash
# Terminal 1 - Worker
celery -A celery_worker.celery_app worker --loglevel=info

# Terminal 2 - Flower (interface web de monitoramento)
celery -A celery_worker.celery_app flower --port=5555

# Terminal 3 - API
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

Acesse o Flower em: http://localhost:5555

## 📚 Usando a API

### URLs importantes:
- **API**: http://localhost:8000
- **Documentação (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints Síncronos (resposta imediata)

#### GET /seasons
Retorna lista de temporadas disponíveis:
```bash
curl http://localhost:8000/seasons
```

#### GET /health
Verifica status da API:
```bash
curl http://localhost:8000/health
```

### Endpoints Assíncronos (processamento em background)

#### POST /async/games/{season_id}
Inicia extração de jogos de uma temporada em background:
```bash
curl -X POST "http://localhost:8000/async/games/58766?transform_data=false"
```

Resposta:
```json
{
  "task_id": "abc123-def456-...",
  "season_id": 58766,
  "status": "processing",
  "message": "Task iniciada. Use GET /tasks/{task_id} para verificar o status"
}
```

#### POST /async/games
Inicia extração de TODOS os jogos em background (operação demorada):
```bash
curl -X POST "http://localhost:8000/async/games?transform_data=false"
```

#### GET /tasks/{task_id}
Verifica o status de uma task:
```bash
curl http://localhost:8000/tasks/abc123-def456-...
```

Respostas possíveis:

**Em processamento:**
```json
{
  "task_id": "abc123...",
  "state": "PROGRESS",
  "progress": {
    "current": 20,
    "total": 38,
    "status": "Extraindo rodada 20..."
  }
}
```

**Concluída:**
```json
{
  "task_id": "abc123...",
  "state": "SUCCESS",
  "result": {
    "status": "completed",
    "season_id": 58766,
    "total_games": 380,
    "games": [...]
  }
}
```

**Falha:**
```json
{
  "task_id": "abc123...",
  "state": "FAILURE",
  "error": "Erro ao processar..."
}
```

#### DELETE /tasks/{task_id}
Cancela uma task em execução:
```bash
curl -X DELETE http://localhost:8000/tasks/abc123-def456-...
```

## 🔄 Fluxo de Uso Típico

1. **Iniciar extração de uma temporada:**
```bash
# Fazer requisição POST para iniciar a task
RESPONSE=$(curl -s -X POST "http://localhost:8000/async/games/58766")
TASK_ID=$(echo $RESPONSE | jq -r '.task_id')
echo "Task ID: $TASK_ID"
```

2. **Monitorar progresso:**
```bash
# Pode consultar múltiplas vezes
curl http://localhost:8000/tasks/$TASK_ID
```

3. **Obter resultado:**
```bash
# Quando state = "SUCCESS", o resultado está no campo "result"
curl http://localhost:8000/tasks/$TASK_ID | jq '.result'
```

## ⚙️ Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` (opcional):
```bash
REDIS_URL=redis://localhost:6379/0
```

### Configuração do Celery

Edite `celery_worker.py` para ajustar:
- `task_time_limit`: Tempo máximo de execução (padrão: 1 hora)
- `task_soft_time_limit`: Tempo de soft limit (padrão: 55 min)
- Timezone (padrão: America/Sao_Paulo)

## 📊 Monitoramento

### Logs

**Celery Worker:**
```bash
tail -f logs/celery_worker.log
```

**API (se usando o script start.sh):**
Os logs aparecem diretamente no console.

### Flower

Interface web para monitorar tasks do Celery:
```bash
celery -A celery_worker.celery_app flower --port=5555
```

Acesse: http://localhost:5555

## 🐛 Troubleshooting

### Redis não está rodando
```bash
# Verificar se Redis está rodando
redis-cli ping
# Deve retornar: PONG

# Se não estiver rodando:
sudo systemctl start redis  # Linux
brew services start redis   # Mac
```

### Celery Worker não inicia
```bash
# Verificar se todas as dependências estão instaladas
pip install -r requirements.txt

# Tentar iniciar com mais verbosidade
celery -A celery_worker.celery_app worker --loglevel=debug
```

### Task fica em PENDING
- Verifique se o Celery Worker está rodando
- Verifique se o Redis está acessível
- Verifique os logs do Worker

## 📝 Estrutura do Projeto

```
etl-statistics/
├── api.py                 # FastAPI application
├── celery_worker.py       # Celery tasks
├── extractor.py           # Extração de dados
├── transform.py           # Transformação de dados
├── load.py               # Carregamento no banco
├── main.py               # Script ETL original
├── requirements.txt       # Dependências
├── start.sh              # Script de inicialização
└── logs/                 # Logs (criado automaticamente)
```

## 🔗 Links Úteis

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Celery Docs](https://docs.celeryproject.org/)
- [Redis Docs](https://redis.io/docs/)
- [Flower Docs](https://flower.readthedocs.io/)

## 📄 Licença

Este projeto é de código aberto.
