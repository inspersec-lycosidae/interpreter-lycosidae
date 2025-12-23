import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.logger import (
    configure_development_logging, 
    configure_production_logging, 
    get_structured_logger
)

# Routers
from app.routers import (
    auth, 
    competitions,
    scoreboard, 
    exercises, 
    containers, 
    solves, 
    tags, 
    attendance
)

# Logging
if os.getenv("ENVIRONMENT", "development") == "production":
    configure_production_logging()
else:
    configure_development_logging()

app_logger = get_structured_logger("main")

app = FastAPI(
    title="Lycosidae Interpreter API",
    description="Camada de persistência e abstração de dados para a plataforma Lycosidae CTF",
    version="1.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Registo de todos os módulos da API
app.include_router(auth.router)
app.include_router(competitions.router)
app.include_router(scoreboard.router)
app.include_router(exercises.router)
app.include_router(containers.router)
app.include_router(solves.router)
app.include_router(tags.router)
app.include_router(attendance.router)

@app.on_event("startup")
def on_startup():
    """
    Evento disparado ao iniciar a aplicação.
    Garante que as tabelas do MariaDB são criadas/atualizadas.
    """
    app_logger.info("Iniciando Interpreter Lycosidae", service="lycosidae-interpreter")
    init_db()
    app_logger.info("Base de dados sincronizada e aplicação online", service="lycosidae-interpreter")

@app.get("/", tags=["health"])
def read_root():
    """
    Health check para monitorização da VPS.
    """
    return {
        "status": "online", 
        "service": "lycosidae-interpreter",
        "version": "1.0.0",
        "active_modules": [
            "auth", "competitions", "scoreboard", 
            "exercises", "containers", "solves", "tags", "attendance"
        ]
    }