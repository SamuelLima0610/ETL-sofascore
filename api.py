from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from etl.extractor import Extractor
from etl.load import Load

import app_dependencies as deps
from routers.general import router as general_router
from routers.games import router as games_router
from routers.tasks import router as tasks_router
from utils.database import Database

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa recursos na startup e limpa no shutdown."""
    print("Inicializando Extractor...")
    deps.extractor = Extractor()
    print("Extractor inicializado com sucesso!")
    print("Inicializando Load...")
    deps.database = Database()
    deps.load = Load(deps.database)
    print("Load inicializado com sucesso!")
    yield
    print("Encerrando aplicação...")
    if deps.database is not None:
        deps.database.disconnect()
        deps.load = None
    deps.extractor = None

app = FastAPI(
    title="ETL Statistics API",
    description="API para extração de estatísticas de futebol do SofaScore com processamento em background via Celery",
    version="2.0.0",
    lifespan=lifespan
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(general_router)
app.include_router(games_router)
app.include_router(tasks_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
