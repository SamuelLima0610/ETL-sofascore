````markdown
# Exemplos de Uso da API - cURL

## 1. Health Check

```bash
curl http://localhost:8000/health
```

## 2. Obter Torneios

```bash
curl http://localhost:8000/tournaments
```

## 3. Buscar jogos salvos (filtros)

O endpoint `GET /games/{category}` permite enviar filtros via query params. Alguns filtros comuns:

- `season` (int)
- `round` (int)
- `home_team` (string)
- `away_team` (string)

Exemplo:

```bash
curl "http://localhost:8000/games/football?season=58766&round=10&home_team=Flamengo"
```

Resposta (resumo):

```json
{
  "count": 2,
  "filters": {"season": 58766, "round": 10, "home_team": "Flamengo"},
  "games": [ /* jogos */ ]
}
```

Observações:

- Valores numéricos são convertidos automaticamente para `int` ou `float`.
- Strings são comparadas por igualdade exata.

## 3. Obter Temporadas (síncrono)

Repare que `GET /seasons` exige query params: `slug_tournament`, `tournament_id`, `country`.

```bash
curl "http://localhost:8000/seasons?slug_tournament=brasileirao-serie-a&tournament_id=325&country=brazil"
```

## 4. Extração Assíncrona de uma Temporada

### Iniciar a extração

```bash
# Substitua 325 pelo ID do torneio e 58766 pelo ID da temporada desejada
curl -X POST "http://localhost:8000/async/games/325/58766?transform_data=false"
```

### Verificar o status da task

```bash
curl http://localhost:8000/tasks/<task_id>
```

## 5. Extração Assíncrona (todas as temporadas de um torneio)

```bash
curl -X POST "http://localhost:8000/async/games?slug_tournament=brasileirao-serie-a&id_tournament=325&country=brazil&transform_data=false"
```

## 6. Script de monitoramento (exemplo)

```bash
TASK_ID=$(curl -s -X POST "http://localhost:8000/async/games/325/58766?transform_data=false" | jq -r '.task_id')
while true; do
  STATUS=$(curl -s http://localhost:8000/tasks/$TASK_ID)
  echo $STATUS | jq '.'
  STATE=$(echo $STATUS | jq -r '.state')
  if [ "$STATE" = "SUCCESS" ] || [ "$STATE" = "FAILURE" ]; then
    break
  fi
  sleep 2
done
```

## 7. Cancelar uma Task

```bash
curl -X DELETE http://localhost:8000/tasks/<task_id>
```

````
