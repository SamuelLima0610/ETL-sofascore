````markdown
# ETL Statistics — Guia Celery & Background Jobs

Este documento complementa o README principal com tudo o que você precisa para orquestrar tarefas em background usando Celery + Redis.

## Componentes
- **API (`api.py`)**: expõe os endpoints que disparam e acompanham tasks.
- **Worker (`celery_worker.py`)**: contém as tasks `extract_games_by_season`, `extract_all_games` e `get_seasons`.
- **ETL (`etl/*.py`)**: utilizado internamente pelas tasks para extrair, transformar e salvar os dados.

## Pré-requisitos e variáveis
- Python 3.8+
- Redis disponível em `REDIS_URL` (ex.: `redis://localhost:6379/0`).
- MongoDB configurado via `USER_DB`, `PASSWORD_DB` e `MONGODB_COLLECTION` no `.env` para que o loader grave os jogos.

## Subindo os serviços

1. Execute `./quickstart.sh` para preparar a `venv`, instalar dependências e validar o Redis.
2. Inicie tudo com `./start.sh` (ativa a `venv`, verifica o Redis, inicia o worker e a API). Logs do worker vão para `logs/celery_worker.log`.

### Execução manual

```bash
source venv/bin/activate

# Worker
celery -A celery_worker.celery_app worker --loglevel=info

# API (outro terminal)
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000

# (Opcional) Flower
celery -A celery_worker.celery_app flower --port=5555
```

## Tasks disponíveis

| Task | Endpoint que dispara | Descrição |
| --- | --- | --- |
| `get_seasons_task` | `POST /async/seasons` | Busca temporadas dos torneios suportados (útil para descobrir IDs recentes). |
| `extract_games_by_season_task` | `POST /async/games/season` | Extrai uma temporada específica, transforma e salva no MongoDB se ainda não existir. |
| `extract_all_games_task` | `POST /async/games` | Percorre todas as temporadas de um torneio (ou uma lista filtrada) e salva apenas jogos novos. |

Cada task emite estados `PENDING`, `PROGRESS`, `SUCCESS` ou `FAILURE`. Durante o `PROGRESS`, meta informa mensagens como "X jogos extraídos".

## Exemplos de uso

```bash
# Assíncrono por temporada
curl -X POST http://localhost:8000/async/games/season \
  -H "Content-Type: application/json" \
  -d '{"tournament_id":325,"season_id":58766}'

# Assíncrono para todo o torneio (opcionalmente filtrando IDs de temporada)
curl -X POST http://localhost:8000/async/games \
  -H "Content-Type: application/json" \
  -d '{"slug_tournament":"brasileirao-serie-a","tournament_id":325,"country":"brazil","length_tournaments":[58766,58767]}'

# Status da task
curl http://localhost:8000/tasks/<task_id>

# Cancelamento
curl -X DELETE http://localhost:8000/tasks/<task_id>
```

## Monitoramento
- **Flower** (`celery -A celery_worker.celery_app flower --port=5555`): dashboard web para acompanhar fila, retries e resultados.
- **Logs**: `logs/celery_worker.log` (worker) e console da API. Ajuste o loglevel com `--loglevel=debug` se precisar de mais detalhes.

## Boas práticas
- Mantenha o Redis saudável (limpe chaves antigas com `redis-cli FLUSHDB` em ambientes de teste).
- Use o endpoint `GET /tasks/{task_id}` antes de disparar novas tarefas para evitar duplicidade.
- Respeite os limites da API do SofaScore (veja a seção de limitações no README principal) e distribua cargas extensas em múltiplas execuções.

````
