from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from application.database import engine, Base
from . import auth, chat, agents, drive
# [New] Import Models explicitly to ensure tables are created
from services.orchestrator.db.tables import ChatLog
from services.ai_hub.db.tables import Agent
from services.ai_drive.db.tables import Document

# TODO: Import Routers (etc.
# from api import etc


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시: 테이블 생성 및 DB 연결
    print("시스템 시작: 데이터베이스 테이블 생성 중...")
    Base.metadata.create_all(bind=engine)
    print("시스템 시작: PostgreSQL, Redis, Milvus 연결 중...")
    yield
    # 종료 시: 연결 닫기
    print("시스템 종료: 연결 닫는 중...")

app = FastAPI(
    title="ISOR AI Platform",
    description="오케스트레이터 및 RAG 기반 엔터프라이즈 AI 에이전트 시스템",
    version="1.0.0",
    lifespan=lifespan
)

# 라우터 포함
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(agents.router)
app.include_router(drive.router)  # AI Drive 라우터 추가

# CORS 미들웨어 (개발 환경에서는 전체 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to ISOR AI Platform API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "components": {"postgres": "unknown", "redis": "unknown", "milvus": "unknown"}}
