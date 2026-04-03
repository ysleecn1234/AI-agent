"""
AI 드라이브 - 문서 처리 파이프라인
업로드 → 파싱 → 청킹 → 임베딩 → 저장
"""

import os
import uuid
import time
import shutil
from typing import Dict, Any, List, Optional
from pathlib import Path

from services.ai_drive.utils.file_parser import FileParser
from services.ai_drive.utils.chunker import TextChunker
from services.ai_drive.core.embedding import EmbeddingGenerator
from services.ai_drive.core.pii_detector import PIIDetector
from services.ai_drive.db.milvus_client import MilvusClient
from services.ai_drive.db.postgres_client import PostgresClient
from services.ai_drive.core.cost_manager import CostManager
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
        self.pii_detector = PIIDetector()
        self.milvus_client = MilvusClient()
        self.postgres_client = PostgresClient()
        self.orchestrator = orchestrator
        self.cost_logger = get_cost_logger()
        self.cost_calculator = get_cost_calculator()
        
        # [Storage] 원본 파일 저장소 초기화
        self.storage_dir = os.path.join(os.getcwd(), "services/ai_drive/storage")
        os.makedirs(self.storage_dir, exist_ok=True)

    def _get_user_pii_settings(self, user_id: str) -> Dict[str, Any]:
        """사용자의 PII 설정을 DB에서 조회"""
        try:
            from application.database import SessionLocal, UserSettings
            db = SessionLocal()
            settings = db.query(UserSettings).filter(
                UserSettings.user_id == user_id
            ).first()
            db.close()
            
            if settings:
                return {
                    "mode": settings.privacy_mode,
                    "detection_items": settings.detection_items,
                }
        except Exception as e:
            print(f"  ⚠️ PII 설정 조회 실패 (기본값 사용): {e}")
        
        # 기본값: 모든 항목 감지 + 차단 모드
        return {
            "mode": "block",
            "detection_items": None,  # None이면 PIIDetector가 모든 항목 감지
        }

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
        file_ext = file_type
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
            
            # [Storage] 원본 파일 영구 저장 (Copy temp file -> storage/doc_id_filename)
            # doc_id를 먼저 생성해야 하므로, create_document 호출 전에 임시 doc_id를 생성하거나,
            # create_document 호출 후 doc_id를 받아 파일 저장 및 DB 업데이트를 해야 함.
            # 여기서는 일단 doc_id를 먼저 생성하고, 파일 저장 후 DB에 file_path를 업데이트하는 방식으로 진행.
            # 또는, doc_id를 uuid로 미리 생성하고 create_document에 전달. 여기서는 후자를 택함.
            
            # doc_id를 미리 생성
            new_doc_id = str(uuid.uuid4())

            original_filename = os.path.basename(file_path)
            # temp prefix 제거 시도 (예: 'tmp_12345_original.pdf' -> 'original.pdf')
            if '_' in original_filename and original_filename.startswith('tmp_'):
                parts = original_filename.split('_', 2) # Split at most twice
                if len(parts) > 2:
                    original_filename = parts[2]
                else: # If it's like 'tmp_12345'
                    original_filename = original_filename # Keep as is or handle differently

            perm_file_name = f"{new_doc_id}_{original_filename}"
            perm_file_path = os.path.join(self.storage_dir, perm_file_name)
            
            db_file_path = "" # Default to empty if copy fails
            try:
                shutil.copy2(file_path, perm_file_path)
                print(f"[Storage] 원본 파일 저장 완료: {perm_file_path}")
                db_file_path = perm_file_path # DB에는 영구 저장 경로 기록

                # [New] PDF 자동 변환 (오피스 파일의 경우 미리보기용)
                ext = os.path.splitext(original_filename)[1].lower()
                if ext in [".docx", ".pptx", ".xlsx"]:
                    print(f"  → 오피스 파일 감지됨. PDF 변환 시작...")
                    import subprocess
                    try:
                        outdir = os.path.dirname(perm_file_path)
                        subprocess.run([
                            "libreoffice", "--headless", "--convert-to", "pdf",
                            perm_file_path, "--outdir", outdir
                        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        
                        generated_pdf_name = os.path.splitext(os.path.basename(perm_file_path))[0] + ".pdf"
                        generated_pdf_path = os.path.join(outdir, generated_pdf_name)
                        target_pdf_path = perm_file_path + ".pdf"
                        
                        if os.path.exists(generated_pdf_path):
                            shutil.move(generated_pdf_path, target_pdf_path)
                            print(f"  → 미리보기용 PDF 변환 완료: {target_pdf_path}")
                    except Exception as pdf_err:
                        print(f"  ⚠️ PDF 변환 실패 (미리보기 불가): {pdf_err}")

            except Exception as e:
                print(f"[Storage] 파일 저장 실패 (무시): {e}")
                # 실패 시 임시 경로 유지 (주의: 곧 삭제될 수 있음)
                # 또는 아예 저장 경로를 기록하지 않음. 여기서는 빈 문자열로 처리.
                db_file_path = "" # If permanent storage fails, don't record a path that might not exist.

            doc_id = self.postgres_client.create_document(
                doc_id=new_doc_id, # 미리 생성한 doc_id 사용
                title=title,
                creator_id=creator_id,
                creator_department=creator_department,
                description=description,
                visibility=visibility,
                file_path=db_file_path,  # 영구 경로 사용
                file_size=file_size,
                file_type=file_ext, # Changed to file_ext
                tags=tags,
                doc_type=doc_type,
                filename=filename,
                source_type="upload", # Changed source_type to "upload"
                version=version,
                parent_doc_id=parent_doc_id
            )
            
            # 상태 업데이트: processing
            self.postgres_client.update_document_status(doc_id, "processing")
            
            # Step 2: 파일 파싱
            print("[Step 2/6] 파일 파싱")
            text = self.file_parser.parse(file_path)
            print(f"  → 추출된 텍스트: {len(text)}자")
            
            # Step 2.5: 개인정보(PII) 감지
            print("[Step 2.5/6] 개인정보 감지")
            pii_settings = self._get_user_pii_settings(creator_id)
            pii_mode = pii_settings.get("mode", "block")
            enabled_items = pii_settings.get("detection_items", None)
            
            pii_result = self.pii_detector.detect(text, enabled_items)
            
            if pii_result["has_pii"]:
                findings_str = ", ".join(
                    f"{f['type']} {f['count']}건" for f in pii_result['findings']
                )
                print(f"  ⚠️ 개인정보 감지: {findings_str}")
                
                if pii_mode == "block":
                    # 차단 모드: 문서 삭제 후 에러 반환
                    self.postgres_client.update_document_status(doc_id, "rejected")
                    # 저장된 파일도 삭제
                    if os.path.exists(perm_file_path):
                        os.remove(perm_file_path)
                    raise ValueError(
                        f"개인정보가 감지되어 업로드가 차단되었습니다: {findings_str}"
                    )
                elif pii_mode == "mask":
                    # 마스킹 모드: PII를 마스킹 처리 후 계속 진행
                    text = self.pii_detector.mask(text, enabled_items)
                    print("  → 개인정보 마스킹 완료")
            else:
                print("  ✅ 개인정보 미감지")
            
            # 전체 텍스트 DB 저장 (검색용 — PII 마스킹 후 텍스트 저장)
            full_text_to_store = text if len(text) < 500000 else text[:500000]
            self.postgres_client.update_full_text(doc_id, full_text_to_store)
            
            # Step 3: 청킹
            print("[Step 3/6] 텍스트 청킹")
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
                    "file_type": file_ext, # Changed to file_ext
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

            
            print(f"[Pipeline] 처리 완료: {duration_ms}ms")
            
            return {
                "success": True,
                "doc_id": doc_id,
                "title": title,
                "filename": filename,
                "file_type": file_ext, # Changed to file_ext
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
            # doc_id를 미리 생성
            doc_id = str(uuid.uuid4())

            # [Storage] 채팅 내용 텍스트 파일 저장 (.txt)
            perm_file_name = f"{doc_id}.txt"
            perm_file_path = os.path.join(self.storage_dir, perm_file_name)
            
            try:
                with open(perm_file_path, 'w', encoding='utf-8') as f:
                    f.write(chat_content)
                print(f"[Storage] 채팅 로그 저장 완료: {perm_file_path}")
            except Exception as e:
                print(f"[Storage] 채팅 저장 실패 (무시): {e}")
                perm_file_path = "" # If permanent storage fails, don't record a path that might not exist.

            # Step 1: 메타데이터 DB 저장
            print("[Step 1/4] 메타데이터 생성")
            self.postgres_client.create_document(
                doc_id=doc_id, # 미리 생성한 doc_id 사용
                creator_id=creator_id,
                creator_department=creator_department,
                title=title,
                description=description,
                visibility=visibility,
                file_path=perm_file_path, # 영구 경로 기록
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
            # doc_id를 미리 생성
            doc_id = str(uuid.uuid4())

            # [Storage] 에이전트 결과 텍스트 파일 저장 (.txt)
            perm_file_name = f"{doc_id}.txt"
            perm_file_path = os.path.join(self.storage_dir, perm_file_name)
            
            try:
                with open(perm_file_path, 'w', encoding='utf-8') as f:
                    f.write(agent_output)
                print(f"[Storage] 에이전트 결과 저장 완료: {perm_file_path}")
            except Exception as e:
                print(f"[Storage] 에이전트 저장 실패 (무시): {e}")
                perm_file_path = "" # If permanent storage fails, don't record a path that might not exist.

            # Step 1: 메타데이터 DB 저장
            print("[Step 1/4] 메타데이터 생성")
            self.postgres_client.create_document(
                doc_id=doc_id, # 미리 생성한 doc_id 사용
                creator_id=creator_id,
                creator_department=creator_department,
                title=title,
                description=description,
                visibility=visibility,
                file_path=perm_file_path, # 영구 경로 기록
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
            tags, keywords, doc_type = self._generate_tags_with_llm(agent_output[:3000])

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
        print(f"\n 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()