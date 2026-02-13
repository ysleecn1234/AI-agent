"""
AI 드라이브 - 문서 처리 파이프라인
업로드 → 파싱 → 청킹 → 임베딩 → 저장
"""

import os
import sys
import uuid
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

# 상위 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from utils.file_parser import FileParser
from utils.chunker import TextChunker
from core.embedding import EmbeddingGenerator
from db.milvus_client import MilvusClient
from db.postgres_client import PostgresClient
from core.cost_manager import CostManager
from services.common.cost_logger import get_cost_logger
from services.orchestrator.cost_calculator import get_cost_calculator
import json

class DocumentPipeline:
    """
    AI 드라이브 문서 처리 파이프라인
    
    처리 흐름:
    1. 파일 파싱 (PDF/DOCX/PPTX/XLSX/TXT/MD/CSV)
    2. 청킹 (1000토큰, 200오버랩)
    3. 임베딩 생성 (OpenAI)
    4. Milvus 저장 (벡터)
    5. PostgreSQL 저장 (메타데이터)
    """
    
    def __init__(self, orchestrator=None):
        self.file_parser = FileParser()
        self.chunker = TextChunker()
        self.embedding_generator = EmbeddingGenerator()
        self.milvus_client = MilvusClient()
        self.postgres_client = PostgresClient()
        self.orchestrator = orchestrator
        self.cost_logger = get_cost_logger()
        self.cost_calculator = get_cost_calculator()

    def process_file_upload(
        self,
        file_path: str,
        creator_id: str,
        creator_department: str,
        title: str = None,
        description: str = "",
        visibility: str = "team",
        tags: List[str] = None,
        doc_type: str = ""
    ) -> Dict[str, Any]:
        """
        파일 업로드 처리 (전체 파이프라인)
        
        Args:
            file_path: 업로드된 파일 경로
            creator_id: 작성자 ID
            creator_department: 작성자 부서
            title: 문서 제목 (없으면 파일명 사용)
            description: 문서 설명
            visibility: 공개범위 (team/company)
            tags: 태그 리스트
            doc_type: 문서 유형
            
        Returns:
            처리 결과 (doc_id, 청크 수, 비용 등)
        """
        start_time = time.time()
        
        # 파일 정보 추출
        path = Path(file_path)
        filename = path.name
        file_type = path.suffix.lower().replace('.', '')
        file_size = path.stat().st_size
        
        if not title:
            title = path.stem  # 확장자 제외한 파일명
        
        print(f"[Pipeline] 문서 처리 시작: {filename}")

        # ===== 버전 관리: 동일 파일명 체크 =====
        version = 1
        parent_doc_id = None

        duplicate = self.postgres_client.check_duplicate_filename(
            filename=filename,
            creator_department=creator_department
        )

        if duplicate.get("exists"):
            old_doc_id = duplicate["doc_id"]
            old_version = duplicate["version"]
            version = old_version + 1
            parent_doc_id = old_doc_id
            
            print(f"  → 기존 문서 발견: v{old_version} → v{version} 업그레이드")
            
            # 이전 버전 아카이브
            self.postgres_client.archive_old_version(old_doc_id)
            
            # Milvus에서 이전 버전 is_latest=False
            self.milvus_client.update_version_status(old_doc_id, old_version)

        try:
            # Step 1: PostgreSQL에 메타데이터 생성 (status: pending)
            print("[Step 1/5] 메타데이터 생성")
            doc_id = self.postgres_client.create_document(
                title=title,
                creator_id=creator_id,
                creator_department=creator_department,
                description=description,
                visibility=visibility,
                file_size=file_size,
                file_type=file_type,
                tags=tags,
                doc_type=doc_type,
                filename=filename,
                source_type="file",
                version=version,
                parent_doc_id=parent_doc_id
            )
            
            # 상태 업데이트: processing
            self.postgres_client.update_document_status(doc_id, "processing")
            
            # Step 2: 파일 파싱
            print("[Step 2/5] 파일 파싱")
            text = self.file_parser.parse(file_path)
            print(f"  → 추출된 텍스트: {len(text)}자")
            
            # Step 3: 청킹
            print("[Step 3/5] 텍스트 청킹")
            chunks = self.chunker.chunk(text)
            print(f"  → 생성된 청크: {len(chunks)}개")

            # 빈 텍스트 처리
            if len(chunks) == 0:
                print("  ⚠️ 추출된 텍스트가 없습니다.")
                self.postgres_client.update_document_status(doc_id, "active")
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                return {
                    "success": True,
                    "doc_id": doc_id,
                    "title": title,
                    "filename": filename,
                    "file_type": file_type,
                    "chunk_count": 0,
                    "total_tokens": 0,
                    "cost_krw": 0,
                    "duration_ms": duration_ms,
                    "warning": "텍스트 추출 없음"
                }
            # AI 태깅 (Orchestrator 사용)
            tags, keywords, doc_type = self._generate_tags_with_llm(text[:3000]) # 텍스트 길이 제한

            # PostgreSQL에 태그 업데이트
            self.postgres_client.update_document_tags(doc_id, tags, keywords, doc_type)

            # Step 4: 임베딩 생성
            print("[Step 4/5] 임베딩 생성")
            embeddings = self.embedding_generator.create_batch(chunks)
            print(f"  → 생성된 임베딩: {len(embeddings)}개")
            
            # Step 5: Milvus 저장
            print("[Step 5/5] 벡터 DB 저장")
            self.milvus_client.insert(
                doc_id=doc_id,
                chunks=chunks,
                embeddings=embeddings,
                visibility=visibility,
                creator_department=creator_department
            )
            
            # 상태 업데이트: active
            self.postgres_client.update_document_status(doc_id, "active")
            
            # chunk_count 업데이트
            self.postgres_client.update_chunk_count(doc_id, len(chunks))
            
            # 처리 시간 계산
            duration_ms = int((time.time() - start_time) * 1000)
            
            # 비용 로그 기록 (임베딩 비용 - API 실제 토큰)
            actual_tokens = self.embedding_generator.last_usage.total_tokens if self.embedding_generator.last_usage else 0
            embed_cost = self.cost_calculator.calculate_cost("text-embedding-3-small", actual_tokens, 0)

            self.cost_logger.log_embedding_cost(
                user_id=creator_id,
                doc_id=doc_id,
                tokens=actual_tokens,
                cost_usd=embed_cost["cost_usd"]["total"],
                cost_krw=embed_cost["cost_krw"]["total"],
            )

            # 크기별 저장 비용
            cost_manager = CostManager()
            storage_cost = cost_manager.calculate_daily_cost(file_size)

            self.cost_logger.log_embedding_cost(
                user_id=creator_id,
                doc_id=doc_id,
                tokens=0,
                cost_usd=storage_cost["daily_cost_krw"] / 1400,
                cost_krw=storage_cost["daily_cost_krw"],
                operation="storage",
            )
            
            print(f"[Pipeline] 처리 완료: {duration_ms}ms")
            
            return {
                "success": True,
                "doc_id": doc_id,
                "title": title,
                "filename": filename,
                "file_type": file_type,
                "chunk_count": len(chunks),
                "total_tokens": actual_tokens,
                "cost_krw": round(embed_cost["cost_krw"]["total"], 4),
                "duration_ms": duration_ms
            }
            
        except Exception as e:
            # 에러 발생 시 상태 업데이트
            if 'doc_id' in locals():
                self.postgres_client.update_document_status(doc_id, "error")
            
            print(f"[Pipeline] 처리 실패: {str(e)}")
            raise
    
    def process_chat_save(
        self,
        chat_content: str,
        creator_id: str,
        creator_department: str,
        title: str,
        description: str = "",
        visibility: str = "team"
    ) -> Dict[str, Any]:
        """
        채팅 결과 저장 처리
        
        Args:
            chat_content: 채팅 내용 (텍스트)
            creator_id: 작성자 ID
            creator_department: 작성자 부서
            title: 문서 제목
            description: 문서 설명
            visibility: 공개범위
            
        Returns:
            처리 결과
        """
        start_time = time.time()
        
        print(f"[Pipeline] 채팅 저장 시작: {title}")
        
        try:
            # Step 1: PostgreSQL에 메타데이터 생성
            print("[Step 1/4] 메타데이터 생성")
            doc_id = self.postgres_client.create_document(
                title=title,
                creator_id=creator_id,
                creator_department=creator_department,
                description=description,
                visibility=visibility,
                file_size=len(chat_content.encode('utf-8')),
                file_type="chat",
                source_type="chat"
            )
            
            self.postgres_client.update_document_status(doc_id, "processing")
            
            # Step 2: 청킹
            print("[Step 2/4] 텍스트 청킹")
            chunks = self.chunker.chunk(chat_content)
            print(f"  → 생성된 청크: {len(chunks)}개")

            # 빈 텍스트 처리
            if len(chunks) == 0:
                self.postgres_client.update_document_status(doc_id, "active")
                duration_ms = int((time.time() - start_time) * 1000)
                return {
                    "success": True,
                    "doc_id": doc_id,
                    "title": title,
                    "chunk_count": 0,
                    "duration_ms": duration_ms,
                    "warning": "텍스트가 비어있습니다"
                }

            # AI 태깅 (Orchestrator 사용)
            tags, keywords, doc_type = self._generate_tags_with_llm(chat_content)

            # PostgreSQL에 태그 업데이트
            self.postgres_client.update_document_tags(doc_id, tags, keywords, doc_type)
            
            # Step 3: 임베딩 생성
            print("[Step 3/4] 임베딩 생성")
            embeddings = self.embedding_generator.create_batch(chunks)
            
            # Step 4: Milvus 저장
            print("[Step 4/4] 벡터 DB 저장")
            self.milvus_client.insert(
                doc_id=doc_id,
                chunks=chunks,
                embeddings=embeddings,
                visibility=visibility,
                creator_department=creator_department
            )
            # chunk_count 업데이트
            self.postgres_client.update_chunk_count(doc_id, len(chunks))

            # 비용 로그 기록 (임베딩 비용 - API 실제 토큰)
            actual_tokens = self.embedding_generator.last_usage.total_tokens if self.embedding_generator.last_usage else 0
            embed_cost = self.cost_calculator.calculate_cost("text-embedding-3-small", actual_tokens, 0)

            self.cost_logger.log_embedding_cost(
                user_id=creator_id,
                doc_id=doc_id,
                tokens=actual_tokens,
                cost_usd=embed_cost["cost_usd"]["total"],
                cost_krw=embed_cost["cost_krw"]["total"],
            )

            # 크기별 저장 비용
            file_size = len(chat_content.encode('utf-8'))
            cost_manager = CostManager()
            storage_cost = cost_manager.calculate_daily_cost(file_size)

            self.cost_logger.log_embedding_cost(
                user_id=creator_id,
                doc_id=doc_id,
                tokens=0,
                cost_usd=storage_cost["daily_cost_krw"] / 1400,
                cost_krw=storage_cost["daily_cost_krw"],
                operation="storage",
            )
            
            self.postgres_client.update_document_status(doc_id, "active")
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            print(f"[Pipeline] 채팅 저장 완료: {duration_ms}ms")
            
            return {
                "success": True,
                "doc_id": doc_id,
                "title": title,
                "chunk_count": len(chunks),
                "duration_ms": duration_ms
            }
            
        except Exception as e:
            if 'doc_id' in locals():
                self.postgres_client.update_document_status(doc_id, "error")
            print(f"[Pipeline] 채팅 저장 실패: {str(e)}")
            raise
    
    def process_agent_save(
        self,
        agent_output: str,
        creator_id: str,
        creator_department: str,
        title: str,
        agent_name: str = "",
        description: str = "",
        visibility: str = "team"
    ) -> Dict[str, Any]:
        """
        에이전트 결과 저장 처리
        
        Args:
            agent_output: 에이전트 출력 결과
            creator_id: 작성자 ID
            creator_department: 작성자 부서
            title: 문서 제목
            agent_name: 에이전트 이름
            description: 문서 설명
            visibility: 공개범위
            
        Returns:
            처리 결과
        """
        start_time = time.time()
        
        print(f"[Pipeline] 에이전트 결과 저장 시작: {title}")
        
        try:
            # Step 1: PostgreSQL에 메타데이터 생성
            print("[Step 1/4] 메타데이터 생성")
            doc_id = self.postgres_client.create_document(
                title=title,
                creator_id=creator_id,
                creator_department=creator_department,
                description=description,
                visibility=visibility,
                file_size=len(agent_output.encode('utf-8')),
                file_type="agent",
                source_type="agent",
                tags=[agent_name] if agent_name else []
            )
            
            self.postgres_client.update_document_status(doc_id, "processing")
            
            # Step 2: 청킹
            print("[Step 2/4] 텍스트 청킹")
            chunks = self.chunker.chunk(agent_output)
            print(f"  → 생성된 청크: {len(chunks)}개")

            # 빈 텍스트 처리
            if len(chunks) == 0:
                self.postgres_client.update_document_status(doc_id, "active")
                duration_ms = int((time.time() - start_time) * 1000)
                return {
                    "success": True,
                    "doc_id": doc_id,
                    "title": title,
                    "chunk_count": 0,
                    "duration_ms": duration_ms,
                    "warning": "텍스트가 비어있습니다"
                }
            
            # AI 태깅
            tags_result = self.auto_tagger.generate_tags(agent_output, title)
            tags = tags_result.get("tags", [])
            keywords = tags_result.get("keywords", [])
            doc_type = tags_result.get("doc_type", "기타")

            # PostgreSQL에 태그 업데이트
            self.postgres_client.update_document_tags(doc_id, tags, keywords, doc_type)

            # Step 3: 임베딩 생성
            print("[Step 3/4] 임베딩 생성")
            embeddings = self.embedding_generator.create_batch(chunks)
            
            # Step 4: Milvus 저장
            print("[Step 4/4] 벡터 DB 저장")
            self.milvus_client.insert(
                doc_id=doc_id,
                chunks=chunks,
                embeddings=embeddings,
                visibility=visibility,
                creator_department=creator_department
            )
            
            # chunk_count 업데이트
            self.postgres_client.update_chunk_count(doc_id, len(chunks))

            # 비용 로그 기록 (임베딩 비용 - API 실제 토큰)
            actual_tokens = self.embedding_generator.last_usage.total_tokens if self.embedding_generator.last_usage else 0
            embed_cost = self.cost_calculator.calculate_cost("text-embedding-3-small", actual_tokens, 0)

            self.cost_logger.log_embedding_cost(
                user_id=creator_id,
                doc_id=doc_id,
                tokens=actual_tokens,
                cost_usd=embed_cost["cost_usd"]["total"],
                cost_krw=embed_cost["cost_krw"]["total"],
            )

            # 크기별 저장 비용
            file_size = len(agent_output.encode('utf-8'))
            cost_manager = CostManager()
            storage_cost = cost_manager.calculate_daily_cost(file_size)

            self.cost_logger.log_embedding_cost(
                user_id=creator_id,
                doc_id=doc_id,
                tokens=0,
                cost_usd=storage_cost["daily_cost_krw"] / 1400,
                cost_krw=storage_cost["daily_cost_krw"],
                operation="storage",
            )

            self.postgres_client.update_document_status(doc_id, "active")
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            print(f"[Pipeline] 에이전트 결과 저장 완료: {duration_ms}ms")
            
            return {
                "success": True,
                "doc_id": doc_id,
                "title": title,
                "chunk_count": len(chunks),
                "duration_ms": duration_ms
            }
            
        except Exception as e:
            if 'doc_id' in locals():
                self.postgres_client.update_document_status(doc_id, "error")
            print(f"[Pipeline] 에이전트 결과 저장 실패: {str(e)}")
            raise
    
    def close(self):
        """리소스 정리"""
        self.milvus_client.close()
        self.postgres_client.close()
        print("[Pipeline] 연결 종료")

    def _generate_tags_with_llm(self, text: str) -> tuple[List[str], List[str], str]:
        """
        Orchestrator를 사용한 태깅 및 메타데이터 추출
        """
        if not self.orchestrator:
            print("[Pipeline] Orchestrator 없음, 태깅 스킵")
            return [], [], "기타"
            
        try:
            # 태깅 태스크 호출
            llm_result = self.orchestrator.call_llm(
                task="tagging",
                prompt=f"다음 텍스트를 분석하여 태그와 키워드, 문서 유형을 추출하세요:\n\n{text[:2000]}"
            )
            
            # JSON 파싱
            response_text = llm_result["content"]
            
            # 마크다운 코드블록 제거
            if "```" in response_text:
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            data = json.loads(response_text.strip())
            
            tags = data.get("tags", [])
            keywords = data.get("keywords", [])
            doc_type = data.get("doc_type", "기타")
            
            return tags, keywords, doc_type
            
        except Exception as e:
            print(f"[Pipeline] 태깅 실패: {e}")
            return [], [], "기타"


# 테스트 코드
if __name__ == "__main__":
    import uuid
    
    print("=" * 80)
    print("DocumentPipeline 테스트")
    print("=" * 80)
    
    try:
        pipeline = DocumentPipeline()
        
        # 테스트용 사용자 정보
        test_user_id = str(uuid.uuid4())
        test_department = "개발팀"
        
        # 채팅 저장 테스트 (파일 없이 테스트 가능)
        print("\n[채팅 저장 테스트]")
        result = pipeline.process_chat_save(
            chat_content="이것은 테스트 채팅 내용입니다. AI 드라이브의 채팅 저장 기능을 테스트합니다. 이 내용은 청킹되어 임베딩으로 변환된 후 Milvus에 저장됩니다.",
            creator_id=test_user_id,
            creator_department=test_department,
            title="테스트 채팅",
            description="파이프라인 테스트용 채팅"
        )
        
        print(f"  → doc_id: {result['doc_id']}")
        print(f"  → 청크 수: {result['chunk_count']}")
        print(f"  → 처리 시간: {result['duration_ms']}ms")
        
        pipeline.close()
        
        print("\n" + "=" * 80)
        print("✓ 테스트 성공!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()