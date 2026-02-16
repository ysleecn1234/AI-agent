"""
AI 드라이브 - PostgreSQL 메타데이터 DB 클라이언트
문서 메타데이터, 활동 로그, 비용 로그 관리
"""

import os
import sys
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy import create_engine, Column, String, Text, Integer, Boolean, DateTime, DECIMAL, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# 공통 모듈 임포트를 위한 경로 설정
current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir))

from services.common.db.models import ActivityLogMixin, CostLogMixin

load_dotenv()

Base = declarative_base()


# ==================== 테이블 정의 (기획서 기준) ====================

class Document(Base):
    """문서 메타데이터 테이블"""
    __tablename__ = 'documents'
    
    doc_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    creator_id = Column(UUID(as_uuid=True), nullable=False)
    creator_department = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    visibility = Column(String(20), default='team')  # team/company/confidential
    status = Column(String(20), default='pending')   # pending/processing/active/archived
    file_size = Column(Integer)
    file_type = Column(String(50))
    version = Column(Integer, default=1)
    parent_doc_id = Column(UUID(as_uuid=True), nullable=True)
    is_latest = Column(Boolean, default=True)
    tags = Column(JSONB, default=list)
    keywords = Column(JSONB, default=list)
    doc_type = Column(String(50))  # 보고서/제안서/회의록 등
    filename = Column(String(255)) # 원본 파일명
    source_type = Column(String(20)) # file/chat/agent
    chunk_count = Column(Integer, default=0)
    file_path = Column(String(500))  # 저장된 파일 경로



class ActivityLog(Base, ActivityLogMixin):
    """활동 로그 테이블 (Common Mixin 사용)"""
    __tablename__ = 'activity_logs'


class CostLog(Base, CostLogMixin):
    """비용 로그 테이블 (Common Mixin 사용)"""
    __tablename__ = 'cost_logs'


# ==================== 클라이언트 클래스 ====================

class PostgresClient:
    """
    PostgreSQL 클라이언트
    - 문서 메타데이터 CRUD
    - 활동 로그 기록
    - 비용 로그 기록
    """
    
    def __init__(self, database_url: str = None):
        """
        Args:
            database_url: PostgreSQL 연결 URL
        """
        if database_url:
            self.database_url = database_url
        else:
            user = os.getenv("POSTGRES_USER", "aiagent")
            password = os.getenv("POSTGRES_PASSWORD", "aiagent123")
            host = os.getenv("POSTGRES_HOST", "localhost")
            port = os.getenv("POSTGRES_PORT", "5433")
            db_name = os.getenv("POSTGRES_DB", "ai_hub")
            
            print(f"[DEBUG] POSTGRES_HOST={host}, PORT={port}, USER={user}, DB={db_name}")
            
            self.database_url = os.getenv(
                "POSTGRES_URL",
                f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
            )
            
            print(f"[DEBUG] Database URL: {self.database_url}")
        
        self.engine = create_engine(self.database_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # 테이블 생성
        self._create_tables()
        
        print(f"✓ PostgreSQL 연결 성공")
    
    def _create_tables(self):
        """테이블 생성 (없으면)"""
        Base.metadata.create_all(self.engine)
        print("✓ 테이블 초기화 완료")
    
    # ==================== 문서 관리 ====================
    
    def create_document(
        self,
        title: str,
        creator_id: str,
        doc_id: str = None,  # [New] 외부에서 생성된 ID 수신
        creator_department: str = "",
        description: str = "",
        visibility: str = "team",
        file_size: int = 0,
        file_type: str = "",
        tags: List[str] = None,
        keywords: List[str] = None,
        doc_type: str = "",
        filename: str = "",
        source_type: str = "file",
        chunk_count: int = 0,
        version: int = 1,
        parent_doc_id: str = None,
        file_path: str = ""
    ) -> str:
        """
        문서 메타데이터 생성
        
        Returns:
            생성된 doc_id
        """
        session = self.Session()
        
        try:
            # doc_id가 없으면 새로 생성
            if not doc_id:
                doc_id = str(uuid.uuid4())
                
            doc = Document(
                doc_id=uuid.UUID(doc_id),
                title=title,
                description=description,
                creator_id=uuid.UUID(creator_id),
                creator_department=creator_department,
                visibility=visibility,
                status='pending',
                file_size=file_size,
                file_type=file_type,
                tags=tags or [],
                keywords=keywords or [],
                doc_type=doc_type,
                filename=filename,
                source_type=source_type,
                chunk_count=chunk_count,
                version=version,
                parent_doc_id=uuid.UUID(parent_doc_id) if parent_doc_id else None,
                file_path=file_path
            )
            
            session.add(doc)
            session.commit()
            
            doc_id = str(doc.doc_id)
            print(f"✓ 문서 생성: {doc_id}")
            
            return doc_id
            
        finally:
            session.close()
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """문서 조회"""
        session = self.Session()
        
        try:
            doc = session.query(Document).filter(
                Document.doc_id == uuid.UUID(doc_id)
            ).first()
            
            if not doc:
                return None
            
            return {
                "doc_id": str(doc.doc_id),
                "title": doc.title,
                "description": doc.description,
                "creator_id": str(doc.creator_id),
                "creator_department": doc.creator_department,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "modified_at": doc.modified_at.isoformat() if doc.modified_at else None,
                "visibility": doc.visibility,
                "status": doc.status,
                "file_size": doc.file_size,
                "file_type": doc.file_type,
                "version": doc.version,
                "parent_doc_id": str(doc.parent_doc_id) if doc.parent_doc_id else None,
                "is_latest": doc.is_latest,
                "tags": doc.tags,
                "keywords": doc.keywords,
                "doc_type": doc.doc_type,
                "filename": doc.filename,
                "source_type": doc.source_type,
                "chunk_count": doc.chunk_count,
                "file_path": doc.file_path,  # [New] 파일 다운로드/서빙을 위해 필요
            }
            
        finally:
            session.close()
    
    def update_document_status(self, doc_id: str, status: str):
        """문서 상태 업데이트"""
        session = self.Session()
        
        try:
            doc = session.query(Document).filter(
                Document.doc_id == uuid.UUID(doc_id)
            ).first()
            
            if doc:
                doc.status = status
                doc.modified_at = datetime.utcnow()
                session.commit()
                print(f"✓ 문서 상태 업데이트: {doc_id} → {status}")
                
        finally:
            session.close()
    
    def update_document_tags(self, doc_id: str, tags: List[str], keywords: List[str] = None, doc_type: str = None):
        """문서 태그/키워드/유형 업데이트"""
        session = self.Session()
        
        try:
            doc = session.query(Document).filter(Document.doc_id == doc_id).first()
            if doc:
                doc.tags = tags
                if keywords:
                    doc.keywords = keywords
                if doc_type:
                    doc.doc_type = doc_type
                session.commit()
                print(f"✓ 태그 업데이트: {doc_id}")
        finally:
            session.close()
    
    def update_chunk_count(self, doc_id: str, chunk_count: int):
        """문서 청크 수 업데이트"""
        session = self.Session()
        
        try:
            doc = session.query(Document).filter(
                Document.doc_id == doc_id
            ).first()
            
            if doc:
                doc.chunk_count = chunk_count
                session.commit()
                print(f"✓ 청크 수 업데이트: {doc_id} → {chunk_count}개")
        finally:
            session.close()
    
    def update_file_path(self, doc_id: str, file_path: str):
        """문서 파일 경로 업데이트"""
        session = self.Session()
        
        try:
            doc = session.query(Document).filter(
                Document.doc_id == doc_id
            ).first()
            
            if doc:
                doc.file_path = file_path
                session.commit()
                print(f"✓ 파일 경로 업데이트: {doc_id}")
        finally:
            session.close()

    def update_document_metadata(
        self,
        doc_id: str,
        title: str = None,
        description: str = None,
        visibility: str = None,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """
        문서 메타데이터 수정 (제목, 설명, 공개범위, 태그)
        
        Args:
            doc_id: 문서 ID
            title: 변경할 제목 (None이면 변경 안 함)
            description: 변경할 설명
            visibility: 변경할 공개범위
            tags: 변경할 태그
            
        Returns:
            {"success": True, "changed_fields": ["title", "visibility"]}
        """
        session = self.Session()
        
        try:
            doc = session.query(Document).filter(
                Document.doc_id == uuid.UUID(doc_id),
                Document.is_latest == True
            ).first()
            
            if not doc:
                return {"success": False, "error": "문서를 찾을 수 없습니다"}
            
            changed_fields = []
            
            if title is not None and title != doc.title:
                doc.title = title
                changed_fields.append("title")
            
            if description is not None and description != doc.description:
                doc.description = description
                changed_fields.append("description")
            
            if visibility is not None and visibility != doc.visibility:
                doc.visibility = visibility
                changed_fields.append("visibility")
            
            if tags is not None and tags != doc.tags:
                doc.tags = tags
                changed_fields.append("tags")
            
            if changed_fields:
                doc.modified_at = datetime.utcnow()
                session.commit()
                print(f"✓ 메타데이터 수정: {doc_id} → {changed_fields}")
            
            return {
                "success": True,
                "changed_fields": changed_fields,
                "doc_id": str(doc.doc_id),
                "title": doc.title,
                "description": doc.description,
                "visibility": doc.visibility,
                "tags": doc.tags,
                "modified_at": doc.modified_at.isoformat()
            }
            
        finally:
            session.close()

    def list_documents(
        self,
        department: str = None, 
        visibility: str = None,
        status: str = "active",
        is_latest: bool = True,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """문서 목록 조회"""
        session = self.Session()
        
        try:
            query = session.query(Document)
            
            if department:
                query = query.filter(Document.creator_department == department)
            if visibility:
                query = query.filter(Document.visibility == visibility)
            if status:
                query = query.filter(Document.status == status)
            if is_latest is not None:
                query = query.filter(Document.is_latest == is_latest)
            
            query = query.order_by(Document.modified_at.desc()).limit(limit)
            
            docs = query.all()
            
            return [
                {
                    "doc_id": str(doc.doc_id),
                    "title": doc.title,
                    "creator_department": doc.creator_department,
                    "visibility": doc.visibility,
                    "status": doc.status,
                    "file_type": doc.file_type,
                    "version": doc.version,
                    "modified_at": doc.modified_at.isoformat() if doc.modified_at else None,
                    "tags": doc.tags
                }
                for doc in docs
            ]
            
        finally:
            session.close()
    
    def delete_document(self, doc_id: str):
        """문서 삭제 (실제 삭제가 아닌 상태 변경)"""
        self.update_document_status(doc_id, "archived")
    
    # ==================== 버전 관리 ====================
    
    def create_new_version(
        self,
        parent_doc_id: str,
        title: str,
        creator_id: str,
        **kwargs
    ) -> str:
        """
        새 버전 생성
        - 이전 버전 is_latest = False
        - 새 버전 생성
        """
        session = self.Session()
        
        try:
            # 이전 버전 찾기
            parent_doc = session.query(Document).filter(
                Document.doc_id == uuid.UUID(parent_doc_id)
            ).first()
            
            if not parent_doc:
                raise ValueError(f"부모 문서를 찾을 수 없음: {parent_doc_id}")
            
            # 이전 버전 is_latest = False
            parent_doc.is_latest = False
            
            # 새 버전 생성
            new_doc = Document(
                title=title,
                description=kwargs.get('description', parent_doc.description),
                creator_id=uuid.UUID(creator_id),
                creator_department=kwargs.get('creator_department', parent_doc.creator_department),
                visibility=kwargs.get('visibility', parent_doc.visibility),
                status='pending',
                file_size=kwargs.get('file_size', 0),
                file_type=kwargs.get('file_type', parent_doc.file_type),
                version=parent_doc.version + 1,
                parent_doc_id=parent_doc.doc_id,
                is_latest=True,
                tags=kwargs.get('tags', parent_doc.tags),
                keywords=kwargs.get('keywords', parent_doc.keywords),
                doc_type=kwargs.get('doc_type', parent_doc.doc_type)
            )
            
            session.add(new_doc)
            session.commit()
            
            new_doc_id = str(new_doc.doc_id)
            print(f"✓ 새 버전 생성: v{new_doc.version} ({new_doc_id})")
            
            return new_doc_id
            
        finally:
            session.close()
    
    def get_version_history(self, doc_id: str) -> List[Dict[str, Any]]:
        """버전 히스토리 조회"""
        session = self.Session()
        
        try:
            # 최신 문서 찾기
            doc = session.query(Document).filter(
                Document.doc_id == uuid.UUID(doc_id)
            ).first()
            
            if not doc:
                return []
            
            # 루트 문서 찾기
            root_id = doc.doc_id
            while doc.parent_doc_id:
                doc = session.query(Document).filter(
                    Document.doc_id == doc.parent_doc_id
                ).first()
                if doc:
                    root_id = doc.doc_id
                else:
                    break
            
            # 모든 버전 조회 (루트부터)
            versions = []
            current_id = root_id
            
            while current_id:
                doc = session.query(Document).filter(
                    Document.doc_id == current_id
                ).first()
                
                if doc:
                    versions.append({
                        "doc_id": str(doc.doc_id),
                        "version": doc.version,
                        "title": doc.title,
                        "is_latest": doc.is_latest,
                        "created_at": doc.created_at.isoformat() if doc.created_at else None
                    })
                    
                    # 다음 버전 찾기
                    next_doc = session.query(Document).filter(
                        Document.parent_doc_id == doc.doc_id
                    ).first()
                    current_id = next_doc.doc_id if next_doc else None
                else:
                    break
            
            return versions
            
        finally:
            session.close()
    
    # ==================== 활동 로그 ====================
    
    def log_activity(
        self,
        user_id: str,
        action: str,
        user_name: str = "",
        doc_id: str = None,
        success: bool = True,
        ip_address: str = "",
        details: Dict = None,
        duration_ms: int = None,
    ):
        """활동 로그 기록"""
        session = self.Session()
        
        try:
            log = ActivityLog(
                user_id=uuid.UUID(user_id),
                user_name=user_name,
                doc_id=uuid.UUID(doc_id) if doc_id else None,
                action=action,
                success=success,
                ip_address=ip_address,
                details=details or {},
                duration_ms=duration_ms
            )
            
            session.add(log)
            session.commit()
            
        finally:
            session.close()
    
    def get_activity_logs(
        self,
        user_id: str = None,
        doc_id: str = None,
        action: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """활동 로그 조회"""
        session = self.Session()
        
        try:
            query = session.query(ActivityLog)
            
            if user_id:
                query = query.filter(ActivityLog.user_id == uuid.UUID(user_id))
            if doc_id:
                query = query.filter(ActivityLog.doc_id == uuid.UUID(doc_id))
            if action:
                query = query.filter(ActivityLog.action == action)
            
            query = query.order_by(ActivityLog.timestamp.desc()).limit(limit)
            
            logs = query.all()
            
            return [
                {
                    "log_id": str(log.log_id),
                    "user_id": str(log.user_id),
                    "user_name": log.user_name,
                    "doc_id": str(log.doc_id) if log.doc_id else None,
                    "action": log.action,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                    "success": log.success,
                    "details": log.details
                }
                for log in logs
            ]
            
        finally:
            session.close()
    
    # ==================== 비용 로그 ====================
    
    def log_cost(
        self,
        user_id: str,
        operation: str,
        tokens_used: int = 0,
        cost_usd: float = 0,
        cost_krw: float = 0,
        doc_id: str = None,
        model_name: str = ""
    ):
        """비용 로그 기록"""
        session = self.Session()
        
        try:
            log = CostLog(
                user_id=uuid.UUID(user_id),
                doc_id=uuid.UUID(doc_id) if doc_id else None,
                operation=operation,
                tokens_used=tokens_used,
                cost_usd=cost_usd,
                cost_krw=cost_krw,
                model_name=model_name
            )
            
            session.add(log)
            session.commit()
            
        finally:
            session.close()
    
    def get_cost_summary(
        self,
        user_id: str = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """비용 요약 조회"""
        session = self.Session()
        
        try:
            query = session.query(CostLog)
            
            if user_id:
                query = query.filter(CostLog.user_id == uuid.UUID(user_id))
            if start_date:
                query = query.filter(CostLog.timestamp >= start_date)
            if end_date:
                query = query.filter(CostLog.timestamp <= end_date)
            
            logs = query.all()
            
            total_tokens = sum(log.tokens_used for log in logs)
            total_usd = sum(float(log.cost_usd) for log in logs)
            total_krw = sum(float(log.cost_krw) for log in logs)
            
            # 작업별 집계
            by_operation = {}
            for log in logs:
                if log.operation not in by_operation:
                    by_operation[log.operation] = {
                        "count": 0,
                        "tokens": 0,
                        "cost_krw": 0
                    }
                by_operation[log.operation]["count"] += 1
                by_operation[log.operation]["tokens"] += log.tokens_used
                by_operation[log.operation]["cost_krw"] += float(log.cost_krw)
            
            return {
                "total_requests": len(logs),
                "total_tokens": total_tokens,
                "total_cost_usd": round(total_usd, 6),
                "total_cost_krw": round(total_krw, 2),
                "by_operation": by_operation
            }
            
        finally:
            session.close()
    
    def check_duplicate_filename(self, filename: str, creator_department: str) -> Dict[str, Any]:
        """
        동일 파일명 문서 확인 (버전 관리용)
        
        Returns:
            존재하면: {"exists": True, "doc_id": "...", "version": 2}
            없으면: {"exists": False}
        """
        session = self.Session()
        
        try:
            doc = session.query(Document).filter(
                Document.filename == filename,
                Document.creator_department == creator_department,
                Document.is_latest == True
            ).first()
            
            if doc:
                return {
                    "exists": True,
                    "doc_id": str(doc.doc_id),
                    "version": doc.version,
                    "title": doc.title
                }
            else:
                return {"exists": False}
        finally:
            session.close()


    def get_version_history(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        문서 버전 히스토리 조회
        (parent_doc_id 체인 따라가기)
        """
        session = self.Session()
        
        try:
            history = []
            
            # 현재 문서 조회
            current = session.query(Document).filter(
                Document.doc_id == doc_id
            ).first()
            
            if not current:
                return []
            
            # 같은 파일명의 모든 버전 조회
            all_versions = session.query(Document).filter(
                Document.filename == current.filename,
                Document.creator_department == current.creator_department,
                Document.title == current.title
            ).order_by(Document.version.desc()).all()
            
            for doc in all_versions:
                history.append({
                    "doc_id": str(doc.doc_id),
                    "title": doc.title,
                    "version": doc.version,
                    "is_latest": doc.is_latest,
                    "status": doc.status,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "modified_at": doc.modified_at.isoformat() if doc.modified_at else None
                })
            
            return history
            
        finally:
            session.close()


    def archive_old_version(self, doc_id: str):
        """이전 버전 아카이브 처리"""
        session = self.Session()
        
        try:
            doc = session.query(Document).filter(
                Document.doc_id == doc_id
            ).first()
            
            if doc:
                doc.is_latest = False
                doc.status = "archived"
                session.commit()
                print(f"✓ 이전 버전 아카이브: {doc_id}")
        finally:
            session.close()

    def get_old_archives(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        N일 이상 된 아카이브 문서 조회
        
        Args:
            days: 기준 일수 (기본 30일)
            
        Returns:
            삭제 대상 문서 리스트
        """
        from datetime import timedelta
        
        session = self.Session()
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            docs = session.query(Document).filter(
                Document.status == "archived",
                Document.modified_at < cutoff_date
            ).all()
            
            return [
                {
                    "doc_id": str(doc.doc_id),
                    "title": doc.title,
                    "file_path": doc.file_path,
                    "modified_at": doc.modified_at.isoformat() if doc.modified_at else None
                }
                for doc in docs
            ]
            
        finally:
            session.close()

    def hard_delete_document(self, doc_id: str):
        """
        문서 완전 삭제 (DB에서 실제 삭제)
        
        Args:
            doc_id: 삭제할 문서 ID
        """
        session = self.Session()
        
        try:
            doc = session.query(Document).filter(
                Document.doc_id == uuid.UUID(doc_id)
            ).first()
            
            if doc:
                session.delete(doc)
                session.commit()
                print(f"✓ 문서 완전 삭제: {doc_id}")
        finally:
            session.close()

    def close(self):
        """연결 종료"""
        self.engine.dispose()
        print("✓ PostgreSQL 연결 종료")


# ==================== 테스트 코드 ====================

if __name__ == "__main__":
    print("=" * 80)
    print("PostgresClient 테스트")
    print("=" * 80)
    
    try:
        client = PostgresClient()
        
        # 테스트용 사용자 ID
        test_user_id = str(uuid.uuid4())
        
        # 1. 문서 생성 테스트
        print("\n[문서 생성 테스트]")
        doc_id = client.create_document(
            title="테스트 문서",
            creator_id=test_user_id,
            creator_department="개발팀",
            description="테스트용 문서입니다.",
            visibility="team",
            file_size=1024,
            file_type="pdf",
            tags=["테스트", "개발"],
            doc_type="보고서"
        )
        print(f"생성된 doc_id: {doc_id}")
        
        # 2. 문서 조회 테스트
        print("\n[문서 조회 테스트]")
        doc = client.get_document(doc_id)
        print(f"제목: {doc['title']}")
        print(f"상태: {doc['status']}")
        print(f"태그: {doc['tags']}")
        
        # 3. 상태 업데이트 테스트
        print("\n[상태 업데이트 테스트]")
        client.update_document_status(doc_id, "active")
        doc = client.get_document(doc_id)
        print(f"새 상태: {doc['status']}")
        
        # 4. 활동 로그 테스트
        print("\n[활동 로그 테스트]")
        client.log_activity(
            user_id=test_user_id,
            action="upload",
            user_name="테스트유저",
            doc_id=doc_id,
            details={"file_name": "test.pdf"}
        )
        logs = client.get_activity_logs(user_id=test_user_id, limit=5)
        print(f"로그 수: {len(logs)}")
        
        # 5. 비용 로그 테스트
        print("\n[비용 로그 테스트]")
        client.log_cost(
            user_id=test_user_id,
            operation="embedding",
            tokens_used=1000,
            cost_usd=0.00002,
            cost_krw=0.028,
            doc_id=doc_id
        )
        summary = client.get_cost_summary(user_id=test_user_id)
        print(f"총 비용: {summary['total_cost_krw']}원")
        
        # 6. 문서 삭제 (아카이브)
        print("\n[문서 삭제 테스트]")
        client.delete_document(doc_id)
        doc = client.get_document(doc_id)
        print(f"삭제 후 상태: {doc['status']}")
        
        client.close()
        
        print("\n" + "=" * 80)
        print("✓ 테스트 성공!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()