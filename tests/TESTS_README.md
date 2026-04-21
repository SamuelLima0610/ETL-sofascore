# Guide de Testes do ETL Statistics API

## Estrutura de Testes

Os testes estão organizados em:

```
tests/
├── __init__.py                 # Package initialization
├── conftest.py                 # Configuração pytest e fixtures compartilhadas
├── test_routers_general.py     # Testes do router general
├── test_routers_games.py       # Testes do router games
├── test_routers_tasks.py       # Testes do router tasks
├── test_utils.py               # Testes de utilitários (tournaments, process)
├── test_schemas.py             # Testes dos schemas Pydantic
├── test_models.py              # Testes dos modelos (Extractor, Load, Database)
├── test_integration.py         # Testes de integração
└── TESTS_README.md             # Este arquivo
```

## Instalação de Dependências para Testes

1. **Certifique-se que o ambiente virtual está ativado:**
```bash
source venv/bin/activate
```

2. **Instale as dependências de teste:**
```bash
pip install pytest pytest-asyncio httpx
```

## Rodando os Testes

### Rodar todos os testes:
```bash
pytest tests/
```

### Rodar com verbose:
```bash
pytest tests/ -v
```

### Rodar testes de um arquivo específico:
```bash
pytest tests/test_routers_general.py -v
```

### Rodar um teste específico:
```bash
pytest tests/test_routers_general.py::TestGeneralRouter::test_health_check_healthy -v
```

### Rodar com coverage (cobertura de código):
```bash
pip install pytest-cov
pytest tests/ --cov=. --cov-report=html
```

### Rodar testes em paralelo:
```bash
pip install pytest-xdist
pytest tests/ -n auto
```

## Estrutura dos Testes

### Fixtures (em `conftest.py`)

- **`mock_extractor`**: Mock do componente Extractor
- **`mock_database`**: Mock do componente Database  
- **`mock_load`**: Mock do componente Load
- **`setup_dependencies`**: Configura as dependências globais da app
- **`client`**: Cliente TestClient do FastAPI

### Padrão de Testes

Cada arquivo de teste segue este padrão:

```python
import pytest

@pytest.mark.asyncio
class TestClassName:
    """Descrição dos testes."""
    
    def test_specific_functionality(self, client, setup_dependencies):
        """Testa uma funcionalidade específica."""
        # Arrange
        expected_value = "something"
        
        # Act
        response = client.get("/endpoint")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["key"] == expected_value
```

## Cobertura de Testes

### Router General (`test_routers_general.py`)
- ✅ Root endpoint
- ✅ Health check
- ✅ Busca de torneios
- ✅ Busca de times
- ✅ Busca de temporadas
- ✅ Busca de predições
- ✅ Validação de dependências

### Router Games (`test_routers_games.py`)
- ✅ Busca de jogos simples
- ✅ Busca com filtros
- ✅ Operadores de comparação (gte, lte, gt, lt, eq, ne)
- ✅ Parsing de valores (int, float, string)
- ✅ Múltiplas categorias
- ✅ Tratamento de erros

### Router Tasks (`test_routers_tasks.py`)
- ✅ Disparo de tasks assíncronas
- ✅ Busca de status de tasks
- ✅ Estados: PENDING, PROGRESS, SUCCESS, FAILURE
- ✅ Cancelamento de tasks
- ✅ Predição assíncrona

### Utils (`test_utils.py`)
- ✅ Funções de torneios
- ✅ Parsing de valores
- ✅ Cálculos de resultados
- ✅ Agregação de dados
- ✅ Busca de imagens de times

### Schemas (`test_schemas.py`)
- ✅ Validação de SeasonExtractionRequest
- ✅ Validação de AllSeasonsExtractionRequest
- ✅ Validação de PredictionRequest
- ✅ Validação de tipos

### Modelos (`test_models.py`)
- ✅ Inicialização de Extractor
- ✅ Inicialização de Database
- ✅ Inicialização de Load
- ✅ Operações básicas

## Mock e Patches

Os testes usam `unittest.mock` para:

1. **Mockar dependências externas:**
   - Database (MongoDB)
   - Extractor (Web scraping)
   - Celery (Task queue)
   - Requests HTTP

2. **Patch de módulos:**
   ```python
   with patch('routers.tasks.get_seasons_task') as mock_task:
       mock_task.delay.return_value = MagicMock(id="test-id")
   ```

## Boas Práticas

### ✅ Faça
- Use fixtures para reutilizar mocks
- Organize testes em classes por funcionalidade
- Use nomes descritivos nos testes
- Teste casos de sucesso e erro
- Use `@pytest.mark.asyncio` para testes assíncronos
- Limpe recursos após testes (fixtures com yield)

### ❌ Não Faça
- Não faça testes que dependam de recursos externos reais
- Não misture testes unitários com testes de integração
- Não deixe dados de teste no banco
- Não ignore erros de teste

## Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'pytest'"
```bash
pip install pytest pytest-asyncio
```

### Erro: "Cannot connect to MongoDB"
Isso é esperado! Os testes usam mocks, não dados reais. Se quiser testar com dados reais, crie testes de integração separados.

### Erro: "Fixture not found"
Certifique-se que `conftest.py` está no diretório `tests/` e importa corretamente.

## CI/CD Integration

Para integrar em um pipeline CI/CD, use:

```bash
# Rodar testes com coverage
pytest tests/ --cov=. --cov-report=xml --cov-report=term

# Fail se coverage < 80%
pytest tests/ --cov=. --cov-fail-under=80
```

## Recursos Adicionais

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
