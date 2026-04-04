"""
AI 드라이브 - 문서별 채팅 (간소화 버전)
특정 문서 1개에 대해서만 질문/답변

간소화 파이프라인 (2단계):
- Step 1: Researcher (Milvus 검색)
- Step 2: Reasoner (GPT-4o-mini 답변 생성)
- 민감정보 마스킹 (정규식)

※ 비용 75% 절감 (LLM 4회 → 1회)
"""

import os
import re
import time
from typing import Dict, List, Any
from dotenv import load_dotenv
from services.common.cost_logger import get_cost_logger
from services.orchestrator.cost_calculator import get_cost_calculator

load_dotenv()


class DocumentChat:
    """
    문서별 채팅 - 간소화 파이프라인
    
    사용자가 특정 문서를 클릭하면,
    해당 문서에 대해서만 질문/답변 가능
    """
    
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator  # 중앙 LLM 호출용

        # orchestrator가 있으면 중앙 관제 모드, 없으면 기존 방식
        if self.orchestrator:
            self.use_mock = False
        else:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            self.use_mock = False
            if not self.openai_api_key:
                self.use_mock = True

            if not self.use_mock:
                self._init_clients()
        
        # DB 클라이언트
        from services.ai_drive.db.postgres_client import PostgresClient
        from services.ai_drive.db.milvus_client import MilvusClient
        
        self.postgres_client = PostgresClient()
        self.milvus_client = MilvusClient()
        self.cost_logger = get_cost_logger()
        self.cost_calculator = get_cost_calculator()
    
    def _init_clients(self):
        """LLM 클라이언트 초기화"""
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        except Exception as e:
            self.use_mock = True
    
    def chat(
        self,
        doc_id: str,
        question: str,
        user_id: str = "anonymous"
    ) -> Dict[str, Any]:
        """
        문서별 채팅 메인 함수
        
        Args:
            doc_id: 문서 ID
            question: 사용자 질문
            user_id: 사용자 ID
            
        Returns:
            {
                "answer": "답변 내용",
                "sources": ["참조한 청크들"],
                "processing_time_ms": 500
            }
        """
        start_time = time.time()

        # Step 0: 문서 정보 조회
        doc_meta = self.postgres_client.get_document(doc_id)
        if not doc_meta:
            return {"error": "문서를 찾을 수 없습니다", "answer": None}

        doc_title = doc_meta.get("title", "문서")

        # Step 1: Researcher - 해당 문서에서 관련 청크 찾기
        relevant_chunks = self._search_chunks(doc_id, question, user_id)
        
        if not relevant_chunks:
            return {
                "answer": "해당 문서에서 관련 내용을 찾을 수 없습니다.",
                "sources": [],
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
        
        # Step 2: Reasoner - 답변 생성 (할루시네이션 방지 프롬프트)
        raw_answer = self._generate_answer(question, relevant_chunks, doc_title)

        # 민감정보 마스킹 (정규식)
        final_answer, is_safe = self._mask_sensitive_info(raw_answer)
        
        # 처리 시간 계산
        processing_time = int((time.time() - start_time) * 1000)
        
        # 비용 로그 기록
        self._log_cost(doc_id, user_id, processing_time)
        
        result = {
            "answer": final_answer,
            "sources": [chunk[:100] + "..." for chunk in relevant_chunks[:3]],
            "doc_title": doc_title,
            "processing_time_ms": processing_time,
            "model_used": "gpt-4o-mini"
        }

        return result
    
    # ==================== Step 1: 청크 검색 ====================
    
    def _search_chunks(self, doc_id: str, question: str, user_id: str) -> List[str]:
        """해당 문서에서 관련 청크 검색"""
        try:
            from services.ai_drive.core.embedding import EmbeddingGenerator
            
            embedding_gen = EmbeddingGenerator()
            question_embedding = embedding_gen.create(question)
            
            # 비용 로깅 (API 실제 토큰)
            try:
                actual_tokens = embedding_gen.last_usage.total_tokens if embedding_gen.last_usage else 0
                embed_cost = self.cost_calculator.calculate_cost("text-embedding-3-small", actual_tokens, 0)

                self.cost_logger.log_embedding_cost(
                    user_id=user_id,
                    tokens=actual_tokens,
                    cost_usd=embed_cost["cost_usd"]["total"],
                    cost_krw=embed_cost["cost_krw"]["total"],
                    doc_id=doc_id,
                    operation="chat_embedding",
                )
            except Exception as log_error:
                pass
            
            # Milvus에서 해당 doc_id의 청크만 검색
            results = self.milvus_client.search_by_doc_id(
                doc_id=doc_id,
                query_embedding=question_embedding,
                top_k=5
            )
            
            # 청크 텍스트만 추출
            chunks = [r.get("chunk_text", "") for r in results if r.get("chunk_text")]
            return chunks

        except Exception as e:
            return self._fallback_get_chunks(doc_id)
    
    def _fallback_get_chunks(self, doc_id: str) -> List[str]:
        """Fallback: Milvus에서 doc_id로 청크 직접 조회"""
        try:
            results = self.milvus_client.get_chunks_by_doc_id(doc_id)
            return [r.get("chunk_text", "") for r in results if r.get("chunk_text")]
        except Exception:
            return []
    
    # ==================== Step 2: 답변 생성 ====================
    
    def _generate_answer(
        self,
        question: str,
        chunks: List[str],
        doc_title: str
    ) -> str:
        """답변 생성 (GPT-4o-mini) - 할루시네이션 방지 프롬프트"""
        if self.use_mock:
            return self._mock_answer(question, chunks, doc_title)
        
        # 청크들을 컨텍스트로 결합
        context = "\n\n---\n\n".join(chunks)
        
        # 할루시네이션 방지 강화 프롬프트
        prompt = f"""당신은 '{doc_title}' 문서에 대해 답변하는 AI입니다.

## 규칙 (반드시 지켜주세요!):
1. 아래 문서 내용만 사용해서 답변하세요
2. 문서에 없는 내용은 절대 추측하지 마세요
3. 모르면 "해당 내용은 문서에 없습니다"라고 답하세요
4. 답변은 명확하고 간결하게 작성하세요

## 문서 내용:
{context}

## 질문:
{question}

## 답변:"""
        
        try:
            llm_result = self.orchestrator.call_llm(
                task="doc_chat",
                prompt=prompt,
            )
            return llm_result["content"]

        except Exception as e:
            return self._mock_answer(question, chunks, doc_title)
    
    def _mock_answer(self, question: str, chunks: List[str], doc_title: str) -> str:
        """Mock 답변"""
        if not chunks:
            return "해당 문서에서 관련 내용을 찾을 수 없습니다."
        
        return f"""'{doc_title}' 문서를 기반으로 답변드립니다.

{chunks[0][:500]}...

(Mock 모드: 실제 LLM 연동 시 더 정확한 답변이 생성됩니다)"""
    
    # ==================== 민감정보 마스킹 ====================
    
    def _mask_sensitive_info(self, text: str) -> tuple:
        """민감정보 마스킹 (정규식)"""
        is_safe = True
        masked_text = text
        
        # 전화번호 마스킹
        phone_pattern = r'01[0-9]-?\d{3,4}-?\d{4}'
        if re.search(phone_pattern, masked_text):
            masked_text = re.sub(phone_pattern, '[전화번호 마스킹]', masked_text)
            is_safe = False
        
        # 주민번호 마스킹
        ssn_pattern = r'\d{6}-?[1-4]\d{6}'
        if re.search(ssn_pattern, masked_text):
            masked_text = re.sub(ssn_pattern, '[주민번호 마스킹]', masked_text)
            is_safe = False
        
        # 이메일 마스킹
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        if re.search(email_pattern, masked_text):
            masked_text = re.sub(email_pattern, '[이메일 마스킹]', masked_text)
            is_safe = False
        
        # 계좌번호 마스킹
        account_pattern = r'\d{3,4}-?\d{2,4}-?\d{4,6}'
        if re.search(account_pattern, masked_text):
            masked_text = re.sub(account_pattern, '[계좌번호 마스킹]', masked_text)
            is_safe = False
        
        return masked_text, is_safe
    
    # ==================== 비용 로깅 ====================
    
    def _log_cost(self, doc_id: str, user_id: str, processing_time: int):
        """비용 로그 기록 - LLM 비용은 orchestrator.call_llm()에서 자동 처리"""
        # orchestrator 모드에서는 LLM 비용 로깅이 call_llm()에서 자동 처리됨
        # 이 메서드는 향후 활동 로그 등 추가 용도로 유지
        pass
    
    def close(self):
        """리소스 정리"""
        self.postgres_client.close()
        self.milvus_client.close()