"""
AI Drive 서비스 통합
--------------------
App 쉘(FastAPI)과 AI Drive 로직을 연결합니다.
"""

import os
import shutil
import tempfile
from typing import List, Dict, Any
from fastapi import UploadFile

# 팀 코드 연동
from services.ai_drive.pipeline import DocumentPipeline
from services.ai_drive.db.postgres_client import PostgresClient

class AIDriveService:
    def __init__(self):
        # 팀 모듈 초기화
        self.pipeline = DocumentPipeline()
        self.db_client = PostgresClient()

    def get_user_storage_usage(self, user_id: str) -> Dict:
        """
        저장소 사용량 통계를 조회합니다.
        TODO: PostgresClient에서 실제 집계 로직 구현 필요.
        현재는 더미 값을 반환하거나 지원될 경우 계산할 수 있습니다.
        """
        # Feature-H에는 아직 직접적인 'get_usage' 메서드가 없습니다.
        return {"used_mb": 150, "limit_mb": 1000, "file_count": 24}

    def fetch_available_knowledge(self, user_id: str) -> List[Dict]:
        """
        RAG에 사용할 수 있는 문서 목록을 반환합니다.
        Agent 생성 마법사 2단계에서 사용됩니다.
        """
        # ai_drive DB 클라이언트 호출
        docs = self.db_client.list_documents(
            status="active",
            visibility="team" # 당분간 팀 공개를 기본값으로 설정
        )
        
        # 프론트엔드용 포맷 변환
        return [
            {
                "id": doc["doc_id"],
                "title": doc["title"],
                "type": (doc.get("file_type") or "DOC").upper(),
                "created_at": doc.get("created_at")
            }
            for doc in docs
        ]

    def upload_document(self, user_id: str, file: UploadFile, department: str = "General"):
        """
        파이프라인을 통한 파일 업로드 처리.
        """
        try:
            # 1. 임시 파일 저장 (파이프라인이 파일 경로를 요구함)
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = tmp.name

            # 2. Feature-H 파이프라인 호출
            result = self.pipeline.process_file_upload(
                file_path=tmp_path,
                creator_id=user_id,
                creator_department=department,
                title=file.filename,
                visibility="team"
            )
            
            # 3. 정리 (Cleanup)
            os.remove(tmp_path)
            
            return result

        except Exception as e:
            print(f"[Drive Service] Upload Error: {e}")
            raise e

drive_service = AIDriveService()
