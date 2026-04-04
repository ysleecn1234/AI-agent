"""
활동 로그 DB 기록 모듈
- 사용자 행위(업로드, 검색, 채팅 등)를 activity_logs 테이블에 INSERT
- application 계층에서만 호출 (3계층 원칙 준수)
"""

import os
import uuid
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()


class ActivityLogger:
    """
    활동 로그를 DB에 기록하는 유틸리티
    - application 계층(drive_service, agent_service, orchestrator_service)에서 호출
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
    
    def log(
        self,
        user_id: str,
        action: str,
        details: dict = None,
        success: bool = True,
        duration_ms: int = None,
        doc_id: Optional[str] = None,
        user_name: str = ""
    ):
        """
        활동 로그를 DB에 기록
        
        Args:
            user_id: 사용자 ID
            action: 행위 (upload, search, chat, delete, create_draft, publish_agent 등)
            details: 상세 정보 dict
            success: 성공 여부
            duration_ms: 처리 시간 (ms)
            doc_id: 문서 ID (선택)
            user_name: 사용자 이름 (선택)
        """
        session = None
        try:
            from services.ai_drive.db.postgres_client import ActivityLog
            
            session = self._get_session()
            
            log = ActivityLog(
                user_id=uuid.UUID(user_id),
                action=action,
                details=details or {},
                success=success,
                duration_ms=duration_ms,
                doc_id=uuid.UUID(doc_id) if doc_id else None,
                user_name=user_name,
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
_global_activity_logger: Optional[ActivityLogger] = None


def get_activity_logger() -> ActivityLogger:
    """전역 ActivityLogger 인스턴스 반환"""
    global _global_activity_logger
    if _global_activity_logger is None:
        _global_activity_logger = ActivityLogger()
    return _global_activity_logger