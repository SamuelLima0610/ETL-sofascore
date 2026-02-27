# Exemplos de Uso da API - cURL

## 1. Health Check

```bash
curl http://localhost:8000/health
```

## 2. Obter Temporadas (Síncrono)

```bash
curl http://localhost:8000/seasons
```

## 3. Extração Assíncrona de uma Temporada

### Iniciar a extração
```bash
# Substitua 58766 pelo ID da temporada desejada
curl -X POST "http://localhost:8000/async/games/58766?transform_data=false"
```

Resposta:
```json
{
  "task_id": "abc123-def456-789...",
  "season_id": 58766,
  "status": "processing",
  "message": "Task iniciada. Use GET /tasks/{task_id} para verificar o status"
}
```

### Verificar o status da task
```bash
# Substitua pelo task_id retornado
curl http://localhost:8000/tasks/abc123-def456-789...
```

### Verificar status com formatação JSON (requer jq)
```bash
curl -s http://localhost:8000/tasks/abc123-def456-789... | jq '.'
```

## 4. Extração de Todas as Temporadas (Assíncrono)

```bash
curl -X POST "http://localhost:8000/async/games?transform_data=false"
```

## 5. Monitorar Progresso em Loop

```bash
# Salvar o task_id
TASK_ID=$(curl -s -X POST "http://localhost:8000/async/games/58766" | jq -r '.task_id')

# Monitorar em loop
while true; do
  echo "Status da task: $TASK_ID"
  curl -s http://localhost:8000/tasks/$TASK_ID | jq '.state, .progress'
  echo "---"
  sleep 3
done
```

## 6. Script Completo de Teste

```bash
#!/bin/bash

API_URL="http://localhost:8000"

echo "=== 1. Health Check ==="
curl -s $API_URL/health | jq '.'

echo -e "\n=== 2. Obtendo temporadas ==="
SEASONS=$(curl -s $API_URL/seasons)
echo $SEASONS | jq '.seasons[0:3]'

# Pegar ID da primeira temporada
SEASON_ID=$(echo $SEASONS | jq -r '.seasons[0].id')
echo "Usando temporada: $SEASON_ID"

echo -e "\n=== 3. Iniciando extração assíncrona ==="
RESPONSE=$(curl -s -X POST "$API_URL/async/games/$SEASON_ID?transform_data=false")
TASK_ID=$(echo $RESPONSE | jq -r '.task_id')
echo "Task ID: $TASK_ID"

echo -e "\n=== 4. Monitorando progresso ==="
for i in {1..30}; do
  echo "Tentativa $i/30"
  STATUS=$(curl -s $API_URL/tasks/$TASK_ID)
  STATE=$(echo $STATUS | jq -r '.state')
  echo "Estado: $STATE"
  
  if [ "$STATE" = "SUCCESS" ]; then
    echo "✅ Concluído!"
    echo $STATUS | jq '.result | {total_games, season_id}'
    break
  elif [ "$STATE" = "FAILURE" ]; then
    echo "❌ Erro!"
    echo $STATUS | jq '.error'
    break
  elif [ "$STATE" = "PROGRESS" ]; then
    echo $STATUS | jq '.progress'
  fi
  
  sleep 2
done
```

## 7. Cancelar uma Task

```bash
curl -X DELETE http://localhost:8000/tasks/abc123-def456-789...
```

## 8. Com Transformação de Dados

```bash
# Extrai E transforma os dados
curl -X POST "http://localhost:8000/async/games/58766?transform_data=true"
```

## 9. Obter Resultado Completo

```bash
# Obtém o resultado completo incluindo todos os jogos
TASK_ID="abc123-def456-789..."
curl -s http://localhost:8000/tasks/$TASK_ID | jq '.result.games' > games.json
```

## 10. Verificar Apenas Estado

```bash
curl -s http://localhost:8000/tasks/$TASK_ID | jq -r '.state'
```
