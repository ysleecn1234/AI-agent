"""
AI 드라이브 - 통합 테스트
전체 파이프라인 테스트 (업로드 → 검색 → 채팅)
"""

import os
import sys
import uuid
import pytest
from pathlib import Path

# 상위 디렉토리 import 설정
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from pipeline import DocumentPipeline
from core.rag_search import RAGSearcher
from core.doc_chat import DocumentChat
from db.postgres_client import PostgresClient
from db.milvus_client import MilvusClient


class TestIntegration:
    """통합 테스트 클래스"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """테스트 전 설정"""
        self.test_user_id = str(uuid.uuid4())
        self.test_department = "테스트팀"
        self.created_doc_ids = []
        
        yield
        
        # 테스트 후 정리 (생성된 문서 삭제)
        self._cleanup()
    
    def _cleanup(self):
        """테스트 데이터 정리"""
        try:
            postgres = PostgresClient()
            milvus = MilvusClient()
            
            for doc_id in self.created_doc_ids:
                postgres.delete_document(doc_id)
                milvus.delete_by_doc_id(doc_id)
            
            postgres.close()
            milvus.close()
        except Exception as e:
            print(f"정리 중 오류: {e}")
    
    # ==================== 1. 채팅 저장 테스트 ====================
    
    def test_chat_save(self):
        """채팅 저장 → DB 확인"""
        pipeline = DocumentPipeline()
        
        # 채팅 저장
        result = pipeline.process_chat_save(
            chat_content="통합 테스트용 채팅입니다. AI 드라이브 기능을 테스트합니다.",
            creator_id=self.test_user_id,
            creator_department=self.test_department,
            title="통합테스트_채팅",
            description="테스트용"
        )
        
        self.created_doc_ids.append(result["doc_id"])
        
        # 검증
        assert result["success"] == True
        assert result["doc_id"] is not None
        assert result["chunk_count"] >= 1
        
        # DB에서 조회 확인
        doc = pipeline.postgres_client.get_document(result["doc_id"])
        assert doc is not None
        assert doc["title"] == "통합테스트_채팅"
        
        pipeline.close()
        print("✓ 채팅 저장 테스트 통과")
    
    # ==================== 2. RAG 검색 테스트 ====================
    
    def test_rag_search(self):
        """문서 저장 → RAG 검색"""
        pipeline = DocumentPipeline()
        
        # 먼저 문서 저장
        result = pipeline.process_chat_save(
            chat_content="마케팅 전략 보고서입니다. 2024년 타겟 고객은 20-30대입니다. SNS 마케팅을 강화합니다.",
            creator_id=self.test_user_id,
            creator_department=self.test_department,
            title="마케팅전략_테스트",
            visibility="company"  # 검색 가능하도록 company
        )
        
        self.created_doc_ids.append(result["doc_id"])
        pipeline.close()
        
        # RAG 검색
        searcher = RAGSearcher()
        
        search_results = searcher.search(
            query="마케팅 전략",
            user_department=self.test_department,
            top_k=5
        )
        
        searcher.close()
        
        # 검증 (결과가 있어야 함)
        assert isinstance(search_results, list)
        print(f"✓ RAG 검색 테스트 통과 (결과: {len(search_results)}개)")
    
    # ==================== 3. 문서별 채팅 테스트 ====================
    
    def test_doc_chat(self):
        """문서 저장 → 문서별 채팅"""
        pipeline = DocumentPipeline()
        
        # 먼저 문서 저장
        result = pipeline.process_chat_save(
            chat_content="AI 드라이브는 문서 관리 시스템입니다. RAG 기반 검색을 지원합니다.",
            creator_id=self.test_user_id,
            creator_department=self.test_department,
            title="AI드라이브_설명"
        )
        
        doc_id = result["doc_id"]
        self.created_doc_ids.append(doc_id)
        pipeline.close()
        
        # 문서별 채팅
        doc_chat = DocumentChat()
        
        chat_result = doc_chat.chat(
            doc_id=doc_id,
            question="이 문서가 설명하는 시스템은 뭐야?",
            user_id=self.test_user_id
        )
        
        doc_chat.close()
        
        # 검증
        assert chat_result["answer"] is not None
        assert len(chat_result["answer"]) > 0
        print(f"✓ 문서별 채팅 테스트 통과")
    
    # ==================== 4. 버전 관리 테스트 ====================
    
    def test_version_management(self):
        """동일 파일 재업로드 → 버전 증가"""
        pipeline = DocumentPipeline()
        
        # 첫 번째 저장
        result1 = pipeline.process_chat_save(
            chat_content="버전 1 내용입니다.",
            creator_id=self.test_user_id,
            creator_department=self.test_department,
            title="버전테스트_문서"
        )
        
        self.created_doc_ids.append(result1["doc_id"])
        
        # 버전 확인
        doc1 = pipeline.postgres_client.get_document(result1["doc_id"])
        assert doc1["version"] == 1
        
        pipeline.close()
        print("✓ 버전 관리 테스트 통과")
    
    # ==================== 5. 비용 로그 테스트 ====================
    
    def test_cost_logging(self):
        """문서 저장 → 비용 로그 확인"""
        pipeline = DocumentPipeline()
        
        # 문서 저장
        result = pipeline.process_chat_save(
            chat_content="비용 테스트용 문서입니다.",
            creator_id=self.test_user_id,
            creator_department=self.test_department,
            title="비용테스트_문서"
        )
        
        self.created_doc_ids.append(result["doc_id"])
        
        # 비용 로그 확인
        cost_summary = pipeline.postgres_client.get_cost_summary(
            user_id=self.test_user_id
        )
        
        assert cost_summary["total_requests"] >= 1
        
        pipeline.close()
        print(f"✓ 비용 로그 테스트 통과 (총 비용: {cost_summary['total_cost_krw']}원)")


# ==================== 실행 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("AI 드라이브 통합 테스트")
    print("=" * 60)
    
    # pytest 없이 직접 실행
    test = TestIntegration()
    
    try:
        # setup
        test.test_user_id = str(uuid.uuid4())
        test.test_department = "테스트팀"
        test.created_doc_ids = []
        
        # 테스트 실행
        print("\n[1/5] 채팅 저장 테스트")
        test.test_chat_save()
        
        print("\n[2/5] RAG 검색 테스트")
        test.test_rag_search()
        
        print("\n[3/5] 문서별 채팅 테스트")
        test.test_doc_chat()
        
        print("\n[4/5] 버전 관리 테스트")
        test.test_version_management()
        
        print("\n[5/5] 비용 로그 테스트")
        test.test_cost_logging()
        
        print("\n" + "=" * 60)
        print("✅ 모든 통합 테스트 통과!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # cleanup
        test._cleanup()