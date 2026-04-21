<!-- TESTING_QUICKSTART.md -->
# 🧪 Quick Start - Unit Tests

## ⚡ 30 Segundos para Começar

```bash
# 1. Entre no diretório
cd /home/samuelvitoriolima/Documentos/repositories/etl-statistics

# 2. Ative o ambiente virtual
source venv/bin/activate

# 3. Rode os testes
pytest tests/
```

**Resultado esperado:** ✅ 77 passed in ~2s

---

## 📊 Resumo dos Testes

```
┌─────────────────────────────────────────────────────────────────┐
│                     ETL Statistics API - Tests                  │
├─────────────────────────────────────┬──────┬─────────────────────┤
│ Módulo                              │ Qtd  │ Status              │
├─────────────────────────────────────┼──────┼─────────────────────┤
│ Routers - General                   │  12  │ ✅ PASS             │
│ Routers - Games                     │   9  │ ✅ PASS             │
│ Routers - Tasks                     │   9  │ ✅ PASS             │
│ Utils - Tournaments & Processing    │  23  │ ✅ PASS             │
│ Schemas - Pydantic Validation       │  12  │ ✅ PASS             │
│ Models - ETL Components             │   7  │ ✅ PASS             │
│ Integration Tests                   │   5  │ ✅ PASS             │
├─────────────────────────────────────┼──────┼─────────────────────┤
│ TOTAL                               │  77  │ ✅ ALL PASS         │
└─────────────────────────────────────┴──────┴─────────────────────┘
```

---

## 🚀 Comandos Comuns

### Rodar Todos os Testes
```bash
pytest tests/ -v
```

### Com Coverage Report
```bash
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

### Teste Específico
```bash
pytest tests/test_routers_general.py::TestGeneralRouter::test_health_check_healthy -v
```

### Em Paralelo (mais rápido)
```bash
pip install pytest-xdist
pytest tests/ -n auto
```

### Via Makefile
```bash
make test              # Rodar testes
make test-coverage     # Com coverage
make lint              # Verificar estilo
make clean             # Limpar arquivos
```

### Via Script
```bash
./run_tests.sh all       # Todos com coverage
./run_tests.sh fast      # Rápido
./run_tests.sh file nome # Arquivo específico
```

---

## 📁 Estrutura dos Testes

```
tests/
├── conftest.py                    ← ⭐ FIXTURES AQUI
│   ├── mock_extractor
│   ├── mock_database
│   ├── setup_dependencies
│   └── client
│
├── test_routers_general.py        ← Testes de /health, /tournaments, etc
├── test_routers_games.py          ← Testes de /games com filtros
├── test_routers_tasks.py          ← Testes de tasks assíncronas
├── test_utils.py                  ← Testes de funções auxiliares
├── test_schemas.py                ← Testes de validação Pydantic
├── test_models.py                 ← Testes de Extractor, Database
├── test_integration.py            ← Testes de fluxos completos
└── TESTS_README.md                ← Documentação detalhada
```

---

## 🔍 Exemplo de Teste

```python
# tests/test_routers_general.py

class TestGeneralRouter:
    def test_health_check_healthy(self, client, setup_dependencies):
        """Testa se health check retorna status healthy."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "extractor_ready" in data
        assert "celery_ready" in data
```

---

## 💡 O Que É Testado

### ✅ Endpoints da API
- GET `/health` - Health check
- GET `/tournaments` - Lista de torneios
- GET `/seasons` - Temporadas de um torneio
- GET `/games/{category}` - Jogos com filtros dinâmicos
- GET `/teams/{team_id}` - Informações de time
- POST `/async/games/season` - Extração assíncrona

### ✅ Funcionalidades
- Validação de parâmetros
- Tratamento de erros
- Verificação de dependências
- Parsing de filtros MongoDB
- Operadores de comparação (gte, lte, etc)
- Operações assíncronas com Celery

### ✅ Schemas
- SeasonExtractionRequest
- AllSeasonsExtractionRequest
- PredictionRequest

### ✅ Utilities
- Funções de torneios
- Processamento de dados
- Parsing de valores
- Cálculos de resultados

---

## 🎯 Mocking Pattern

Todos os testes usam **mocks** para não depender de:
- 🚫 MongoDB (Database)
- 🚫 Web scraping (Extractor)
- 🚫 Celery (Task queue)
- 🚫 HTTP requests

Exemplo:
```python
@pytest.fixture
def mock_database():
    mock = Mock()
    mock.read_data = Mock(return_value=[
        {'id': 1, 'name': 'Flamengo'}
    ])
    return mock
```

---

## 📦 Dependências Necessárias

**Core (já instaladas):**
- pytest
- pytest-asyncio
- httpx

**Opcionais:**
```bash
pip install pytest-cov        # Coverage report
pip install pytest-xdist      # Testes paralelos
pip install pytest-watch      # Watch mode
```

---

## ✨ Features Extras

### GitHub Actions CI/CD
Tests rodamautomaticamente em:
- Push para main/develop
- Pull requests
- Python 3.9, 3.10, 3.11

Ver: `.github/workflows/tests.yml`

### Configuração Pytest
Ver: `pytest.ini`

### Dependências de Dev
Ver: `requirements-dev.txt`

---

## 🐛 Troubleshooting

**Error: "No module named pytest"**
```bash
pip install pytest pytest-asyncio
```

**Error: "Cannot connect to MongoDB"**
→ Normal! Os testes usam mocks, não dados reais.

**Tests slow?**
```bash
pytest tests/ -n auto  # Paralelo
```

**Need verbose output?**
```bash
pytest tests/ -vv  # Very verbose
```

---

## 📚 Documentação Completa

Ver arquivo: [tests/TESTS_README.md](tests/TESTS_README.md)

Contém:
- Instalação passo a passo
- Explicação de cada fixture
- Como adicionar novos testes
- Melhorias futuras

---

## 🎉 Result

```
============================ 77 passed in 2.00s =============================

✅ All tests passing!
✅ Ready for production!
✅ CI/CD configured!
```

**Próximo passo:** Consulte a documentação em `tests/TESTS_README.md`
