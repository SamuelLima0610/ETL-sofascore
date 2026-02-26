**Project**: ETL for SofaScore games

- **Description**: ETL pipeline that extracts match data from SofaScore, transforms statistics into a consistent structure, and loads results to a sink. This repository contains the extractor (`[extractor.py](extractor.py)`), transformer (`[transform.py](transform.py)`), and a sample loader (`[loader.py](loader.py)`) to persist transformed data.

**Quick Start**:
- **Prerequisites**: Python 3.8+, virtualenv
- **Install**:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # create if needed: requests beautifulsoup4
```

- **Run**:

```bash
python main.py
```

**Files**:
- **`extractor.py`**: fetches seasons and game data from SofaScore.
- **`transform.py`**: normalizes game statistics into a consistent JSON-friendly structure.
- **`main.py`**: example run flow (extract → transform). To persist results, call the loader from here or run the loader as a separate step.

**Implementing the Load**
- Goal: persist transformed game objects to your desired sink (file, database, data warehouse).

Recommended steps to implement a production loader:
- Decide sink: JSON/CSV (filesystem), SQLite/Postgres, or cloud (S3, BigQuery).
- Create a `Loader` class with a `load(data)` method that accepts the transformed list of games.
- If using a relational DB, implement an idempotent upsert: create tables and use `INSERT ... ON CONFLICT` (Postgres) or replace semantics.
- Add batching and retries for large volumes and transient failures.

**Next steps / Ideas**
- Add a database loader (`loader_db.py`) that writes to Postgres or SQLite.
- Add CLI flags to `main.py` to select sink and season range.
- Add tests for `Transform.transform()` and loader behavior.

If you want, I can implement a DB loader (SQLite or Postgres) and wire it into `main.py`.
