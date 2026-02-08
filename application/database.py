import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. 데이터베이스 설정
POSTGRES_USER = os.getenv("POSTGRES_USER", "in7user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "in7password")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "in7platform")

SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

# 2. 엔진 설정
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 3. 세션 설정
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. 모델을 위한 Base 클래스
Base = declarative_base()

# 5. API를 위한 의존성 주입 (Dependency)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 1. 사용자 테이블 (신원 및 프로필)
# ==========================================
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(50), nullable=False)
    department = Column(String(50), nullable=False)
    
    # 개인화 메모리 (유연성을 위한 JSONB)
    memory = Column(JSONB, nullable=True) 

    # 관계 설정
    agents = relationship("services.ai_hub.db.tables.Agent", back_populates="creator")
    chat_logs = relationship("services.orchestrator.db.tables.ChatLog", back_populates="user")

