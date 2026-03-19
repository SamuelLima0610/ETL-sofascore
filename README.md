````markdown
# ETL Statistics

Pipeline completo para extrair estatísticas de partidas do SofaScore, transformar os dados em um modelo consolidado e persistir tudo em MongoDB, expondo os resultados através de uma API FastAPI e tarefas Celery.

## Destaques
- FastAPI com endpoints síncronos para consultas e estatísticas já salvas.
- Celery + Redis para acionar extrações pesadas em background (por temporada ou campeonato completo).
- Módulos dedicados de ETL: `etl/extractor.py`, `etl/transform.py`, `etl/load.py`.
- Scripts utilitários (`quickstart.sh` e `start.sh`) para preparar ambiente e subir todos os serviços rapidamente.

## Requisitos
- Python 3.8 ou superior
- Redis acessível (broker/backend do Celery)
- MongoDB Atlas ou instância compatível com o driver `pymongo`
- `pip install -r requirements.txt`

## Configuração

1. Crie e ative um ambiente virtual:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure um arquivo `.env` na raiz com as credenciais dos serviços externos:

   ```dotenv
   REDIS_URL=redis://localhost:6379/0
   USER_DB=<mongo_user>
   PASSWORD_DB=<mongo_password>
   MONGODB_COLLECTION=<collection_name>
   ```

   > O loader (`etl/load.py`) usa o cluster `Statistics` e conecta em `mongodb+srv://`. Ajuste conforme a sua instância.

## Scripts úteis

| Script | O que faz |
| --- | --- |
| `quickstart.sh` | Cria/ativa a `venv`, instala dependências e verifica se o Redis está rodando. Ideal para a primeira execução. |
| `start.sh` | Checa Redis, ativa a `venv`, inicia Celery worker (log em `logs/celery_worker.log`) e sobe a API via Uvicorn em background. |

Após rodar o `quickstart.sh`, basta executar `./start.sh` para colocar tudo no ar.

## Executando manualmente

Caso prefira controlar cada processo:

```bash
# Worker Celery
celery -A celery_worker.celery_app worker --loglevel=info

# API FastAPI
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000

# (Opcional) Dashboard Flower
celery -A celery_worker.celery_app flower --port=5555
```

## API

Documentação automática: http://localhost:8000/docs

| Método | Caminho | Descrição |
| --- | --- | --- |
| GET | `/` | Metadados e mapa de endpoints disponíveis. |
| GET | `/health` | Health check (inclui status do extractor e Celery). |
| GET | `/tournaments` | Lista torneios disponíveis por categoria (`football`, `basketball`, ...). |
| GET | `/seasons` | Busca temporadas de um torneio (`slug_tournament`, `tournament_id`, `country`). |
| GET | `/games/{category}` | Consulta partidas salvas em MongoDB aceitando filtros dinâmicos via query string. |
| GET | `/games/{collection}/{id}` | Recupera uma partida específica pelo `id` original do SofaScore. |
| GET | `/versus/{collection}` | Calcula médias e retrospecto entre duas equipes (`team_one`, `team_two`). |
| POST | `/async/prediction` | Inicia task para prever a probabilidade de vitória do confronto (`game_id`, `home_team`, `away_team`, `tournament_id`, `season_id`). |
| POST | `/async/seasons` | Dispara task para coletar temporadas de todos os torneios suportados. |
| POST | `/async/games/season` | Agenda extração de uma temporada (`tournament_id`, `season_id`). |
| POST | `/async/games` | Agenda extração completa de um torneio inteiro (todas as temporadas) com filtros opcionais. |
| GET | `/tasks/{task_id}` | Consulta o estado/resultados de uma task Celery. |
| DELETE | `/tasks/{task_id}` | Efetua cancelamento forçado de uma task em andamento. |

### Filtros dinâmicos (`GET /games/{category}`)
Todos os parâmetros enviados na query string são convertidos automaticamente:

- Dígitos inteiros => `int`
- Valores com ponto => `float`
- Demais => `str`

Exemplo:

```bash
curl "http://localhost:8000/games/football?season=58766&round=10&home_team=Flamengo"
```

Resposta simplificada:

```json
{
  "count": 3,
  "filters": {"season": 58766, "round": 10, "home_team": "Flamengo"},
  "games": [ {"id": 123, "home_team": "Flamengo", "stats": [...] } ]
}
```

### Payloads das tasks

```json
POST /async/games/season
{
  "tournament_id": 325,
  "season_id": 58766
}

POST /async/games
{
  "slug_tournament": "brasileirao-serie-a",
  "tournament_id": 325,
  "country": "brazil",
  "length_tournaments": [58766, 58767]
}
```

Use `GET /tasks/{task_id}` para acompanhar o progresso (estados `PENDING`, `PROGRESS`, `SUCCESS`, `FAILURE`).

## Fluxo ETL
- **Extractor (`etl/extractor.py`)**: abre uma sessão com o SofaScore, lista torneios/temporadas e coleta estatísticas jogo a jogo.
- **Transform (`etl/transform.py`)**: consolida informações relevantes (placar, rodada, stats por categoria) em um dicionário pronto para persistência.
- **Load (`etl/load.py`)**: conecta no cluster MongoDB definido via `.env`, evita duplicatas por temporada/rodada/time e salva apenas jogos novos.
- **Process helpers (`utils/process.py`)**: normaliza estatísticas e calcula médias para o endpoint `/versus`.

## Logs e observabilidade
- `start.sh` grava o worker em `logs/celery_worker.log`; a API permanece no console.
- Ative o Flower para inspecionar tasks em tempo real: `celery -A celery_worker.celery_app flower --port=5555`.

## Testes

```bash
pytest
```

O arquivo `test_api.py` contém smoke tests básicos para os endpoints principais.

## Limitações
- Após ~4k partidas extraídas em sequência, o SofaScore tende a aplicar rate limit temporário. Considere janelas menores ou revezar o IP (VPN/proxy) em execuções massivas.

## Próximos passos sugeridos
- Adicionar loaders alternativos (Postgres/SQLite) além do MongoDB.
- Criar mais testes de integração/cobertura para os endpoints assíncronos.
- Incrementar políticas de retry/backoff no Celery para lidar com instabilidades da API pública.

````
