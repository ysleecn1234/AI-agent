"""
채팅 세션 메타 테이블 생성 마이그레이션

실행 방법 (서버에서):
  python scripts/migrate_chat_session_meta.py

이 스크립트는 chat_session_meta 테이블을 생성합니다.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from application.database import engine, Base
from services.orchestrator.db.tables import ChatSessionMeta

def migrate():
    print("Creating chat_session_meta table...")
    ChatSessionMeta.__table__.create(engine, checkfirst=True)
    print("Done! chat_session_meta table created successfully.")

if __name__ == "__main__":
    migrate()
