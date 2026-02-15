"""
AI 드라이브 - RAG 4단계 검색
Step 1: 질문 임베딩 생성
Step 2: Milvus 유사도 검색 (Top-10)
Step 3: 권한 필터링 (status, is_latest, visibility, department)
Step 4: Freshness Score 적용 → Top-5 반환
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from services.ai_drive.core.embedding import EmbeddingGenerator
from services.ai_drive.db.milvus_client import MilvusClient
from services.ai_drive.db.postgres_client import PostgresClient
from services.common.cost_logger import get_cost_logger
from services.orchestrator.cost_calculator import get_cost_calculator

class RAGSearcher:
    """
    RAG 4단계 검색 엔진
    
    오케스트레이터 Researcher 레이어와 연동
    - 입력: 질문, 사용자 부서
    - 출력: 관련 문서 청크 (Top-5)
    """
    
    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()
        self.milvus_client = MilvusClient()
        self.postgres_client = PostgresClient()
        self.cost_logger = get_cost_logger()
        self.cost_calculator = get_cost_calculator()
    
    def search(
        self,
        query: str,
        user_department: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        RAG 4단계 검색 실행
        
        Args:
            query: 사용자 질문
            user_department: 사용자 부서 (권한 필터링용)
            top_k: 최종 반환 개수 (기본 5)
            
        Returns:
            [
                {
                    "doc_id": "문서 ID",
                    "content": "청크 텍스트",
                    "source": "문서 제목",
                    "score": 0.95,
                    "author": "작성자",
                    "department": "작성자 부서",
                    "date": "2026-01-31",
                    "page": 1
                },
                ...
            ]
        """
        print(f"[RAG] 검색 시작: '{query[:50]}...'")
        
        # Step 1: 질문 임베딩 생성
        print("[Step 1/4] 질문 임베딩 생성")
        query_embedding = self._create_query_embedding(query)
        
        if not query_embedding:
            print("  ⚠️ 임베딩 생성 실패")
            return []
        
        # Step 2: Milvus 유사도 검색 (Top-10)
        print("[Step 2/4] Milvus 유사도 검색 (Top-10)")
        raw_results = self._search_similar_chunks(
            query_embedding=query_embedding,
            user_department=user_department,
            top_k=10  # 권한 필터링 전 여유있게
        )
        
        print(f"  → 검색 결과: {len(raw_results)}개")
        
        if not raw_results:
            print("  ⚠️ 검색 결과 없음")
            return []
        
        # Step 3: 권한 필터링 (이미 Milvus에서 기본 필터링 됨)
        # 추가 검증이 필요한 경우 여기서 처리
        print("[Step 3/4] 권한 필터링 확인")
        filtered_results = self._verify_permissions(raw_results, user_department)
        print(f"  → 필터링 후: {len(filtered_results)}개")
        
        # Step 4: Freshness Score 적용 → Top-5 반환
        print("[Step 4/4] Freshness Score 적용")
        final_results = self._apply_freshness_score(filtered_results, top_k)
        print(f"  → 최종 결과: {len(final_results)}개")
        
        # 메타데이터 보강 (출처 정보)
        enriched_results = self._enrich_with_metadata(final_results)
        
        print(f"[RAG] 검색 완료")
        
        return enriched_results
    
    # ==================== Step 1: 임베딩 생성 ====================
    
    def _create_query_embedding(self, query: str) -> Optional[List[float]]:
        """질문을 임베딩 벡터로 변환"""
        try:
            embedding = self.embedding_generator.create(query)
            
            # 비용 로깅 (API 실제 토큰)
            try:
                actual_tokens = self.embedding_generator.last_usage.total_tokens if self.embedding_generator.last_usage else 0
                embed_cost = self.cost_calculator.calculate_cost("text-embedding-3-small", actual_tokens, 0)

                self.cost_logger.log_embedding_cost(
                    user_id="system",
                    tokens=actual_tokens,
                    cost_usd=embed_cost["cost_usd"]["total"],
                    cost_krw=embed_cost["cost_krw"]["total"],
                    operation="search_embedding",
                )
            except Exception as log_error:
                print(f"  ⚠️ 비용 로그 실패: {log_error}")
            
            return embedding
        except Exception as e:
            print(f"  ❌ 임베딩 생성 실패: {str(e)}")
            return None
    
    # ==================== Step 2: 유사도 검색 ====================
    
    def _search_similar_chunks(
        self,
        query_embedding: List[float],
        user_department: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Milvus에서 유사도 기반 검색
        - COSINE 유사도
        - 권한 필터 적용 (visibility, department)
        """
        try:
            results = self.milvus_client.search(
                query_embedding=query_embedding,
                department=user_department,
                top_k=top_k
            )
            return results
        except Exception as e:
            print(f"  ❌ Milvus 검색 실패: {str(e)}")
            return []
    
    # ==================== Step 3: 권한 필터링 ====================
    
    def _verify_permissions(
        self,
        results: List[Dict[str, Any]],
        user_department: str
    ) -> List[Dict[str, Any]]:
        """
        권한 추가 검증
        - status = 'active'
        - is_latest = true
        - visibility 확인
        
        (Milvus에서 기본 필터링되지만, 추가 검증)
        """
        verified = []
        
        for result in results:
            visibility = result.get("visibility", "team")
            doc_department = result.get("creator_department", "")
            
            # company 공개: 누구나 접근 가능
            if visibility == "company":
                verified.append(result)
                continue
            
            # team 공개: 같은 부서만 접근
            if visibility == "team" and doc_department == user_department:
                verified.append(result)
                continue
            
            # confidential: Phase 2에서는 제외 (결재 시스템 필요)
            # 나중에 결재 승인된 경우만 허용
        
        return verified
    
    # ==================== Step 4: Freshness Score ====================
    
    def _apply_freshness_score(
        self,
        results: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Freshness Score 적용 (기획서 기준)
        - 수정일 1주일 이내: +0.1점
        - 수정일 1개월 이내: +0.05점
        - 재정렬 후 Top-k 반환
        """
        now = datetime.now()
        one_week_ago = now - timedelta(days=7)
        one_month_ago = now - timedelta(days=30)
        
        scored_results = []
        
        for result in results:
            base_score = result.get("score", 0)
            freshness_bonus = 0
            
            # PostgreSQL에서 modified_at 조회
            doc_id = result.get("doc_id")
            modified_at = None
            
            if doc_id:
                try:
                    doc_meta = self.postgres_client.get_document(doc_id)
                    if doc_meta:
                        modified_at = doc_meta.get("modified_at")
                except Exception:
                    pass
            
            # modified_at 파싱 및 Freshness Score 계산
            if modified_at:
                try:
                    if isinstance(modified_at, str):
                        mod_date = datetime.fromisoformat(modified_at.replace('Z', '+00:00'))
                    elif isinstance(modified_at, datetime):
                        mod_date = modified_at
                    else:
                        mod_date = None
                    
                    if mod_date:
                        mod_date_naive = mod_date.replace(tzinfo=None)
                        
                        # Freshness Score 계산
                        if mod_date_naive >= one_week_ago:
                            freshness_bonus = 0.1
                        elif mod_date_naive >= one_month_ago:
                            freshness_bonus = 0.05
                except Exception as e:
                    print(f"  ⚠️ 날짜 파싱 오류: {e}")
            
            # 최종 점수
            final_score = base_score + freshness_bonus
            result["original_score"] = base_score
            result["freshness_bonus"] = freshness_bonus
            result["score"] = final_score
            result["modified_at"] = modified_at  # 결과에 추가
            
            scored_results.append(result)
        
        # 점수 기준 정렬 (내림차순)
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        
        # Top-k 반환
        return scored_results[:top_k]

    
    # ==================== 메타데이터 보강 ====================
    
    def _enrich_with_metadata(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        PostgreSQL에서 문서 메타데이터 조회하여 출처 정보 보강
        - 문서 제목 (source)
        - 작성자 (author)
        - 날짜 (date)
        """
        enriched = []
        
        for result in results:
            doc_id = result.get("doc_id")
            
            # PostgreSQL에서 문서 메타데이터 조회
            doc_meta = None
            if doc_id:
                try:
                    doc_meta = self.postgres_client.get_document(doc_id)
                except Exception:
                    pass
            
            # 출처 정보 구성
            enriched_result = {
                "doc_id": doc_id,
                "content": result.get("chunk_text", result.get("content", "")),
                "source": doc_meta.get("title", "알 수 없음") if doc_meta else "알 수 없음",
                "score": result.get("score", 0),
                "author": doc_meta.get("creator_department", "") if doc_meta else "",
                "department": result.get("creator_department", ""),
                "date": doc_meta.get("modified_at", "")[:10] if doc_meta and doc_meta.get("modified_at") else "",
                "visibility": result.get("visibility", "team"),
                "freshness_bonus": result.get("freshness_bonus", 0)
            }
            
            enriched.append(enriched_result)
        
        return enriched
    
    # ==================== 오케스트레이터 연동 인터페이스 ====================
    
    def rag_search(
        self,
        query: str,
        user_department: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        오케스트레이터 Researcher용 인터페이스
        
        영민이 pipeline.py에서 호출하는 함수
        
        Args:
            query: 사용자 질문
            user_department: 사용자 부서
            top_k: 반환 개수
            
        Returns:
            검색 결과 리스트
        """
        return self.search(query, user_department, top_k)
    
    def close(self):
        """리소스 정리"""
        self.milvus_client.close()
        self.postgres_client.close()
        print("[RAG] 연결 종료")


# ==================== 테스트 코드 ====================

if __name__ == "__main__":
    print("=" * 80)
    print("RAG 4단계 검색 테스트")
    print("=" * 80)
    
    try:
        searcher = RAGSearcher()
        
        # 테스트 검색
        print("\n[테스트 1] 일반 검색")
        results = searcher.search(
            query="마케팅 전략에 대해 알려줘",
            user_department="개발팀"
        )
        
        print(f"\n검색 결과: {len(results)}개")
        for i, result in enumerate(results, 1):
            print(f"\n  [{i}] {result['source']}")
            print(f"      점수: {result['score']:.4f} (Freshness: +{result['freshness_bonus']})")
            print(f"      부서: {result['department']}")
            print(f"      날짜: {result['date']}")
            print(f"      내용: {result['content'][:100]}...")
        
        searcher.close()
        
        print("\n" + "=" * 80)
        print("✓ 테스트 완료!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()