import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from logger import (
    configure_development_logging, 
    configure_production_logging, 
    get_structured_logger
)
from app.routers import auth, competitions, exercises

# Configura logging baseado no ambiente
if os.getenv("ENVIRONMENT", "development") == "production":
    configure_production_logging()
else:
    configure_development_logging()

app_logger = get_structured_logger("main")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(auth.router)
app.include_router(competitions.router)
app.include_router(exercises.router)

@app.on_event("startup")
def on_startup():
    app_logger.info("Iniciando Interpreter Lycosidae", service="lycosidae-interpreter")
    init_db()
    app_logger.info("Aplicação iniciada com sucesso", service="lycosidae-interpreter")

@app.get("/")
def read_root():
    """
    Health check simples
    """

    response_data = {
        "status": "online", 
        "service": "lycosidae-interpreter",
        "modules": ["auth", "competitions", "exercises"]
    }

    app_logger.log_api_response("/", 200, response_data)
    
    return response_data
