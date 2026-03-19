````markdown
# Exemplos de Uso da API (cURL)

Use estes snippets como ponto de partida. Ajuste `tournament_id`, `season_id`, times e coleções de acordo com os dados disponíveis no seu MongoDB.

## 1. Health e metadados

```bash
curl http://localhost:8000/health
curl http://localhost:8000/
```

## 2. Descobrir torneios e temporadas

```bash
# Torneios por categoria
curl http://localhost:8000/tournaments | jq '.'

# Temporadas de um torneio
curl "http://localhost:8000/seasons?slug_tournament=brasileirao-serie-a&tournament_id=325&country=brazil" | jq '.'
```

## 3. Consultar jogos já salvos

```bash
# Filtros dinâmicos
curl "http://localhost:8000/games/football?season=58766&round=10&home_team=Flamengo" | jq '.'

# Buscar um jogo específico (id original da partida)
curl http://localhost:8000/games/football/123456
```

Observações:
- valores numéricos são convertidos para `int`/`float` automaticamente;
- qualquer campo existente no documento pode ser usado como filtro.

## 4. Estatísticas de confronto direto

```bash
curl "http://localhost:8000/versus/football?team_one=Flamengo&team_two=Palmeiras" | jq '.'
```

O retorno contém os ids das temporadas envolvidas, número de jogos como mandante/visitante e médias por categoria de estatísticas.

## 5. Predição de probabilidade de vitória

Dispara uma tarefa assíncrona que treina um modelo de Regressão Logística com os dados da temporada e prevê as probabilidades para o confronto.

```bash
curl -X POST http://localhost:8000/async/prediction \
  -H "Content-Type: application/json" \
  -d '{
    "tournament_id": 325,
    "season_id": 58766,
    "game_id": 1234567,
    "home_team": "Flamengo",
    "away_team": "Palmeiras"
  }' | jq '.'
```

## 6. Extração assíncrona

### Única temporada

```bash
curl -X POST http://localhost:8000/async/games/season \
  -H "Content-Type: application/json" \
  -d '{"tournament_id":325,"season_id":58766}'
```

### Todas as temporadas (com filtro opcional)

```bash
curl -X POST http://localhost:8000/async/games \
  -H "Content-Type: application/json" \
  -d '{"slug_tournament":"brasileirao-serie-a","tournament_id":325,"country":"brazil","length_tournaments":[58766,58767]}'
```

### Assíncrono para temporadas configuradas

```bash
curl -X POST http://localhost:8000/async/seasons
```

## 7. Acompanhar e cancelar tasks

```bash
# Status (mostra PROGRESS, SUCCESS, FAILURE)
curl http://localhost:8000/tasks/<task_id> | jq '.'

# Cancelar
curl -X DELETE http://localhost:8000/tasks/<task_id>
```

## 8. Script shell para monitorar

```bash
TASK_ID=$(curl -s -X POST http://localhost:8000/async/games/season \
  -H "Content-Type: application/json" \
  -d '{"tournament_id":325,"season_id":58766}' | jq -r '.task_id')

while true; do
  STATUS=$(curl -s http://localhost:8000/tasks/$TASK_ID)
  echo "$STATUS" | jq '.'
  STATE=$(echo "$STATUS" | jq -r '.state')
  if [ "$STATE" = "SUCCESS" ] || [ "$STATE" = "FAILURE" ]; then
    break
  fi
  sleep 3
done
```

## 9. Limpeza pós-testes

```bash
# Remover resultados antigos do MongoDB (exemplo usando mongosh)
mongosh "mongodb+srv://<user>:<pass>@cluster.bmwwbf1.mongodb.net/Statistics" \
  --eval 'db.games.deleteMany({season: 58766})'
```

````
