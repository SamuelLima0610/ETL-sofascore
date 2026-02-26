**Project**: ETL for SofaScore games

- **Description**: ETL pipeline that extracts match data from SofaScore, transforms statistics into a consistent structure, and loads results to a sink. This repository contains the extractor (`[extractor.py](extractor.py)`), transformer (`[transform.py](transform.py)`), and a sample loader (`[loader.py](loader.py)`) to persist transformed data.

**Quick Start**:
- **Prerequisites**: Python 3.8+, virtualenv
# ETL Statistics

Este repositório contém um pipeline ETL (Extract, Transform, Load) simples para coletar, transformar e persistir estatísticas de partidas.

## Descrição

O projeto implementa as três etapas principais de um ETL:
- Extração: coleta dados brutos de fontes externas (módulo de extração).
- Transformação: normaliza e estrutura os dados para uso analítico.
- Carga (Load): persiste os dados transformados em um destino (arquivo, banco, etc.).

## Pré-requisitos

- Python 3.8 ou superior
- Virtualenv (opcional, mas recomendado)

## Instalação

1. Criar e ativar um ambiente virtual:

```bash
python -m venv venv
source venv/bin/activate
```

2. Instalar dependências:

```bash
pip install -r requirements.txt
```

## Configuração

Se o projeto usar variáveis de ambiente, coloque-as em um arquivo `.env` na raiz e carregue-as no código com `python-dotenv` (já listado em `requirements.txt` se necessário).

## Uso

Para executar o fluxo principal (extração → transformação → carga mínima de exemplo):

```bash
python main.py
```

O arquivo `main.py` demonstra como orquestrar as etapas. Ajuste conforme seu sink (destino) e parâmetros.

## Estrutura do repositório

- [const.py](const.py): constantes e configurações do projeto.
- [extractor.py](extractor.py): código responsável por extrair/baixar os dados brutos.
- [transform.py](transform.py): lógica de transformação.
- [load.py](load.py): exemplo de rotina de carga (persiste dados transformados).
- [main.py](main.py): script de execução que integra `extractor`, `transform` e `load`.
- [requirements.txt](requirements.txt): dependências do projeto.

## Como estender

- Implementar um loader de produção (por exemplo: SQLite, Postgres, S3, BigQuery).
- Adicionar argumentos de linha de comando em `main.py` para escolher períodos, fontes e sinks.
- Incluir testes unitários para `transform.py` e integração para o fluxo completo.

## Boas práticas recomendadas

- Fazer a carga de forma idempotente (upserts) quando usar banco relacional.
- Implementar paginação, batching e retries se a extração lidar com grande volume de dados.
- Separar credenciais e informações sensíveis em variáveis de ambiente.

## Próximos passos sugeridos

- Posso implementar um loader SQLite de exemplo e integrar no `main.py` se desejar.

---

Se quiser que eu gere um `loader_db.py` ou adicione opções de CLI ao `main.py`, diga qual destino prefere (SQLite ou Postgres). 
