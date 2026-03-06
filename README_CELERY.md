````markdown
# ETL Statistics - Celery + API

Documentação e instruções para executar a API (FastAPI) com processamento em background usando Celery.

## Resumo

- API: `api.py` (FastAPI)
- Tasks/background: `celery_worker.py` (Celery usando Redis como broker/backend)
- Extração/Transformação/Carga: `etl/extractor.py`, `etl/transform.py`, `etl/load.py`

## Pré-requisitos

- Python 3.8+
- Redis (broker para Celery)
- (Opcional) MongoDB se quiser persistir dados via `etl/load.py`

## Instalação

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Variáveis de ambiente úteis

- `REDIS_URL` (ex: `redis://localhost:6379/0`)
- `USER_DB`, `PASSWORD_DB`, `MONGODB_COLLECTION` (para `etl/load.py`)

## Executando

Recomendo usar o `start.sh` que inicia o Celery worker e a API:

```bash
chmod +x start.sh
./start.sh
```

Ou manualmente em terminais separados:

Terminal 1 (Celery Worker):

```bash
celery -A celery_worker.celery_app worker --loglevel=info
```

Terminal 2 (API):

```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 3 (opcional - Flower):

```bash
celery -A celery_worker.celery_app flower --port=5555
```

## Endpoints principais

- `GET /` — metadados e links
- `GET /health` — health check
- `GET /tournaments` — lista torneios
- `GET /seasons` — obter temporadas (query params: `slug_tournament`, `tournament_id`, `country`)
- `GET /games/{category}` — buscar jogos persistidos (query params dinâmicos)
- `GET /versus/{category}` — confronto direto entre duas equipes

GET `/games/{category}` — detalhes rápidos

Aceita filtros via query params (por exemplo: `season`, `round`, `home_team`, `away_team`). Valores numéricos são convertidos automaticamente. Se nenhum filtro for passado, retorna todos os jogos persistidos.

Exemplo:

```bash
curl "http://localhost:8000/games/football?season=58766&home_team=Flamengo"
```
- `POST /async/games/season` — inicia extração de uma temporada em background (body: `tournament_id`, `season_id`)
- `POST /async/games` — inicia extração de todas as temporadas (body: `slug_tournament`, `tournament_id`, `country`, `length_tournaments` opcional com IDs de temporada)
- `GET /tasks/{task_id}` — consultar status/result
- `DELETE /tasks/{task_id}` — cancelar task

## Exemplo rápido (curl)

Iniciar extração de uma temporada (não salva no MongoDB):

```bash
curl -X POST "http://localhost:8000/async/games/season" \
	-H "Content-Type: application/json" \
	-d '{"tournament_id":325,"season_id":58766}'
```

Iniciar extração de uma temporada (salva no MongoDB):

```bash
curl -X POST "http://localhost:8000/async/games/season" \
	-H "Content-Type: application/json" \
	-d '{"tournament_id":325,"season_id":58766}'
```

Iniciar extração de todas as temporadas com filtro opcional de IDs:

```bash
curl -X POST "http://localhost:8000/async/games" \
	-H "Content-Type: application/json" \
	-d '{"slug_tournament":"brasileirao-serie-a","tournament_id":325,"country":"brazil","length_tournaments":[58766,58767]}'
```

Consultar status de task:

```bash
curl http://localhost:8000/tasks/<task_id>
```

## Logs

- Celery: `logs/celery_worker.log` (quando iniciado via `start.sh`)
- API: console (quando iniciado via Uvicorn)

````
