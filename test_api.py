#!/usr/bin/env python3
"""
Script de exemplo para testar a API com Celery
"""

import requests
import time
import json

API_URL = "http://localhost:8000"


def print_section(title):
    """Imprime uma seção formatada"""
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50 + "\n")


def test_health():
    """Testa o endpoint de health check"""
    print_section("1. Health Check")
    
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))


def test_seasons():
    """Testa o endpoint de seasons (síncrono)"""
    print_section("2. Obtendo Temporadas (Síncrono)")
    
    response = requests.get(f"{API_URL}/seasons")
    data = response.json()
    
    print(f"Status: {response.status_code}")
    print(f"Total de temporadas: {len(data['seasons'])}")
    print(f"\nPrimeiras 3 temporadas:")
    for season in data['seasons'][:3]:
        print(f"  - ID: {season['id']}, Ano: {season['year']}")
    
    return data['seasons'][2]['id'] if data['seasons'] else None


def test_async_extraction(season_id):
    """Testa extração assíncrona de jogos"""
    print_section(f"3. Extração Assíncrona (Temporada {season_id})")
    
    # Iniciar a task
    print("Iniciando extração em background...")
    response = requests.post(f"{API_URL}/async/games/{season_id}?transform_data=true")
    data = response.json()
    
    task_id = data['task_id']
    print(f"✅ Task iniciada: {task_id}\n")
    
    # Monitorar o progresso
    print("Monitorando progresso...")
    max_attempts = 60  # 60 tentativas = ~1 minuto
    attempt = 0
    
    while attempt < max_attempts:
        time.sleep(2)  # Aguardar 2 segundos
        
        response = requests.get(f"{API_URL}/tasks/{task_id}")
        task_data = response.json()
        
        state = task_data['state']
        print(f"  [{attempt+1}/{max_attempts}] Estado: {state}", end="")
        
        if state == "PROGRESS":
            progress = task_data.get('progress', {})
            current = progress.get('current', 0)
            total = progress.get('total', 0)
            status = progress.get('status', '')
            print(f" - {current}/{total} - {status}")
        elif state == "SUCCESS":
            print(" - ✅ Concluído!")
            result = task_data['result']
            print(f"\nResultado:")
            print(f"  - Total de jogos: {result['total_games']}")
            print(f"  - Temporada: {result['season_id']}")
            return task_id
        elif state == "FAILURE":
            print(" - ❌ Erro!")
            print(f"  Erro: {task_data.get('error', 'Desconhecido')}")
            return None
        else:
            print()
        
        attempt += 1
    
    print("\n⚠️  Timeout atingido")
    return task_id


def test_get_result(task_id):
    """Obtém o resultado de uma task"""
    print_section(f"4. Obtendo Resultado (Task {task_id})")
    
    response = requests.get(f"{API_URL}/tasks/{task_id}")
    data = response.json()
    
    if data['state'] == 'SUCCESS':
        result = data['result']
        print(f"✅ Task completada com sucesso!")
        print(f"Total de jogos: {result['total_games']}")
        
        if result['games']:
            print(f"\nPrimeiro jogo:")
            game = result['games'][0]
            print(f"  - {game['home_team']} {game['home_score']} x {game['away_score']} {game['away_team']}")
            print(f"  - Rodada: {game['round']}")
    else:
        print(f"Estado atual: {data['state']}")


def main():
    """Função principal"""
    print("\n" + "=" * 50)
    print("  ETL Statistics API - Teste de Integração")
    print("=" * 50)
    print("\nCertifique-se de que a API e o Celery Worker estão rodando!")
    print(f"API URL: {API_URL}")
    
    try:
        # 1. Health check
        test_health()
        
        # 2. Obter temporadas
        season_id = test_seasons()
        
        if not season_id:
            print("❌ Nenhuma temporada encontrada!")
            return
        
        # 3. Extração assíncrona
        task_id = test_async_extraction(season_id)
        
        if task_id:
            # 4. Obter resultado
            test_get_result(task_id)
        
        print_section("✅ Testes Concluídos")
        print("\nPara mais informações, acesse:")
        print(f"  - Documentação: {API_URL}/docs")
        print(f"  - Flower (se disponível): http://localhost:5555")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Erro: Não foi possível conectar à API!")
        print("Certifique-se de que a API está rodando em http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")


if __name__ == "__main__":
    main()
