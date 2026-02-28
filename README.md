````markdown
# ETL Statistics

Este repositório contém um pipeline ETL para coletar, transformar e persistir estatísticas de partidas (fonte: SofaScore).

Resumo rápido:
- Extração: `etl/extractor.py`
- Transformação: `etl/transform.py`
- Carga: `etl/load.py` (exemplo com MongoDB)
- API + tasks: `api.py`, `celery_worker.py`

**Pré-requisitos**
- Python 3.8+
- Redis (broker para Celery) — recomendado para executar tarefas em background
- MongoDB (opcional, usado pelo `Load` se quiser persistir dados)

## Instalação rápida

1. Criar/ativar ambiente virtual:

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Instalar dependências:

```bash
pip install -r requirements.txt
```

3. (Opcional) Criar arquivo `.env` com as variáveis abaixo quando usar MongoDB/Celery:

```
REDIS_URL=redis://localhost:6379/0
USER_DB=<mongo_user>
PASSWORD_DB=<mongo_password>
MONGODB_COLLECTION=<collection_name>
```

## Executando localmente

Guia rápido:

- Usar o script `quickstart.sh` para preparar o ambiente.
- Usar `start.sh` para iniciar o Celery worker e a API (script inicia o worker e o Uvicorn).

Comandos manuais:

```bash
# Iniciar Celery Worker
celery -A celery_worker.celery_app worker --loglevel=info

# Iniciar API (FastAPI / Uvicorn)
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Opcional: Flower para monitorar tarefas
celery -A celery_worker.celery_app flower --port=5555
```

## API e endpoints principais

- `GET /` : informações básicas e links para docs
- `GET /tournaments` : retorna torneios (usa `etl/extractor.py`)
- `GET /seasons` : obter temporadas (query params: `slug_tournament`, `id_tournament`, `country`)
-- `GET /health` : health check

GET `/games` — buscar jogos persistidos

Esse endpoint retorna os jogos já persistidos (MongoDB) e aceita filtros dinâmicos via query params. Exemplos de filtros suportados:

- `season` (int)
- `round` (int)
- `home_team` (string)
- `away_team` (string)
- qualquer outro campo presente nos documentos (ex.: `home_score`, `away_score`)

Comportamento:

- Os query params numéricos são convertidos automaticamente (inteiros ou floats). Strings são usadas como igualdade exata.
- Se nenhum filtro for fornecido, todos os jogos persistidos são retornados.

Exemplo (curl):

```bash
curl "http://localhost:8000/games?season=58766&round=10&home_team=Flamengo"
```

Resposta (exemplo):

```json
{
  "count": 3,
  "filters": {"season": 58766, "round": 10, "home_team": "Flamengo"},
  "games": [ /* lista de jogos */ ]
}
```

- Async (via Celery):
  - `POST /async/seasons`
  - `POST /async/games/{season_id}`?transform_data=true|false
  - `POST /async/games` (query params: `slug_tournament`, `id_tournament`, `country`, `transform_data`)
  - `GET /tasks/{task_id}` : status da task
  - `DELETE /tasks/{task_id}` : cancelar task

Docs auto geradas (Swagger): `http://localhost:8000/docs`

## Estrutura relevante

- `api.py` — aplicação FastAPI que expõe endpoints sync/async
- `celery_worker.py` — tasks Celery que usam `etl/` para extrair/transformar/carregar
- `etl/extractor.py` — extrai dados da SofaScore
- `etl/transform.py` — transforma estatísticas em estrutura consistente
- `etl/load.py` — exemplo de loader para MongoDB
- `const/const_football.py` — listas/constantes de estatísticas
- `start.sh`, `quickstart.sh` — scripts de ajuda

## Testes

- `test_api.py` contém testes básicos para a API (rodar com pytest)

## Próximos passos sugeridos

- Integrar um loader de exemplo (SQLite/Postgres) além do MongoDB
- Adicionar mais testes de integração
- Melhorar tratamento de erros e retries nas tasks Celery

````
