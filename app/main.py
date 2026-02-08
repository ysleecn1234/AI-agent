from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import engine
from . import models
from .api import auth, chat, agents, integrations

# ✅ 주요 라우터 import 완료

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create Tables & Connect to DBs
    print("System Startup: creating database tables...")
    models.Base.metadata.create_all(bind=engine)
    print("System Startup: Connecting to PostgreSQL, Redis, and Milvus...")
    yield
    # Shutdown: Close connections
    print("System Shutdown: Closing connections...")

app = FastAPI(
    title="IN7 AI Platform",
    description="Enterprise AI Agent System with Orchestrator & RAG",
    version="1.0.0",
    lifespan=lifespan
)

# Include Routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(agents.router)
app.include_router(integrations.router)

# CORS Middleware (Allow All for Dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to IN7 AI Platform API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "components": {"postgres": "unknown", "redis": "unknown", "milvus": "unknown"}}
