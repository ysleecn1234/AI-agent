"""
비용 로그 DB 기록 모듈 (인프라 유틸리티)
- LLM 호출 비용을 cost_logs 테이블에 INSERT
- services 계층에서 직접 호출 (횡단 관심사 예외)
"""

import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()


class CostLogger:
    """
    비용 로그를 DB에 기록하는 유틸리티
    - pipeline.py call_llm()에서 호출
    - pipeline.py process_premium()에서 호출
    """
    
    def __init__(self):
        self._engine = None
        self._Session = None
    
    def _get_session(self):
        """DB 세션 lazy 초기화"""
        if self._Session is None:
            user = os.getenv("POSTGRES_USER", "aiagent")
            password = os.getenv("POSTGRES_PASSWORD", "aiagent123")
            host = os.getenv("POSTGRES_HOST", "localhost")
            port = os.getenv("POSTGRES_PORT", "5433")
            db_name = os.getenv("POSTGRES_DB", "ai_hub")
            
            database_url = os.getenv(
                "POSTGRES_URL",
                f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
            )
            
            self._engine = create_engine(database_url)
            self._Session = sessionmaker(bind=self._engine)
        
        return self._Session()
    
    def log_llm_cost(
        self,
        task: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        cost_krw: float,
        user_id: Optional[str] = None,
        doc_id: Optional[str] = None
    ):
        """
        LLM 호출 비용을 DB에 기록
        
        Args:
            task: 작업명 (예: chat_simple, tagging, doc_chat)
            model_name: 사용된 모델명
            input_tokens: 입력 토큰 수
            output_tokens: 출력 토큰 수
            cost_usd: USD 비용
            cost_krw: KRW 비용
            user_id: 사용자 ID (선택)
            doc_id: 문서 ID (선택)
        """
        import uuid
        
        session = None
        try:
            # postgres_client의 CostLog 테이블 재사용
            from services.ai_drive.db.postgres_client import CostLog
            
            session = self._get_session()
            
            log = CostLog(
                user_id=uuid.UUID(user_id) if user_id else uuid.UUID('00000000-0000-0000-0000-000000000000'),
                doc_id=uuid.UUID(doc_id) if doc_id else None,
                operation=f"llm:{task}",
                model_name=model_name,
                tokens_used=input_tokens + output_tokens,
                cost_usd=cost_usd,
                cost_krw=cost_krw,
            )
            
            session.add(log)
            session.commit()
            
        except Exception as e:
            if session:
                session.rollback()
        finally:
            if session:
                session.close()
    
    def log_embedding_cost(
        self,
        user_id: str,
        tokens: int,
        cost_usd: float,
        cost_krw: float,
        model_name: str = "text-embedding-3-small",
        doc_id: Optional[str] = None,
        operation: str = "embedding"
    ):
        """
        임베딩 비용을 DB에 기록
        """
        import uuid
        
        session = None
        try:
            from services.ai_drive.db.postgres_client import CostLog
            
            session = self._get_session()
            
            log = CostLog(
                user_id=uuid.UUID(user_id) if user_id else uuid.UUID('00000000-0000-0000-0000-000000000000'),
                doc_id=uuid.UUID(doc_id) if doc_id else None,
                operation=operation,
                model_name=model_name,
                tokens_used=tokens,
                cost_usd=cost_usd,
                cost_krw=cost_krw,
            )
            
            session.add(log)
            session.commit()
            
        except Exception as e:
            if session:
                session.rollback()
        finally:
            if session:
                session.close()


# 전역 인스턴스
_global_cost_logger: Optional[CostLogger] = None


def get_cost_logger() -> CostLogger:
    """전역 CostLogger 인스턴스 반환"""
    global _global_cost_logger
    if _global_cost_logger is None:
        _global_cost_logger = CostLogger()
    return _global_cost_logger