"""
AI 드라이브 - 문서별 채팅
특정 문서 1개에 대해서만 질문/답변하는 5단계 SLM 파이프라인

모델 조합 (저비용 최적화):
- Router: Gemini 2.0 Flash (의도 파악)
- Researcher: Gemini 2.0 Flash (청크 검색)
- Reasoner: GPT-4o-mini (답변 생성) ← 핵심!
- Synthesizer: Gemini 2.0 Flash (답변 정리)
- Guardrail: Gemini 2.0 Flash (민감정보 체크)
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class DocumentChat:
    """
    문서별 채팅 - 5단계 SLM 파이프라인
    
    사용자가 특정 문서를 클릭하면,
    해당 문서에 대해서만 질문/답변 가능
    """
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GOOGLE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Mock 모드 체크
        self.use_mock = False
        if not self.gemini_api_key:
            print("⚠️ GOOGLE_API_KEY 없음 - Mock 모드")
            self.use_mock = True
        if not self.openai_api_key:
            print("⚠️ OPENAI_API_KEY 없음 - Mock 모드")
            self.use_mock = True
        
        if not self.use_mock:
            self._init_clients()
        
        # DB 클라이언트
        from db.postgres_client import PostgresClient
        from db.milvus_client import MilvusClient
        
        self.postgres_client = PostgresClient()
        self.milvus_client = MilvusClient()
    
    def _init_clients(self):
        """LLM 클라이언트 초기화"""
        try:
            # Gemini
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
            print("✓ Gemini Flash 연결 성공")
            
            # OpenAI
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            print("✓ OpenAI 연결 성공")
            
        except Exception as e:
            print(f"⚠️ LLM 연결 실패: {e}")
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
                "processing_time_ms": 720,
                "model_used": {"router": "gemini", ...}
            }
        """
        start_time = time.time()
        
        print(f"\n[DocChat] 문서별 채팅 시작")
        print(f"  문서: {doc_id}")
        print(f"  질문: {question[:50]}...")
        
        # Step 0: 문서 정보 조회
        doc_meta = self.postgres_client.get_document(doc_id)
        if not doc_meta:
            return {"error": "문서를 찾을 수 없습니다", "answer": None}
        
        doc_title = doc_meta.get("title", "문서")
        print(f"  제목: {doc_title}")
        
        # Step 1: Router - 질문 의도 파악
        print("\n[Step 1/5] Router - 의도 파악")
        intent = self._router(question)
        print(f"  → 의도: {intent}")
        
        # Step 2: Researcher - 해당 문서에서 관련 청크 찾기
        print("\n[Step 2/5] Researcher - 관련 청크 검색")
        relevant_chunks = self._researcher(doc_id, question)
        print(f"  → 관련 청크: {len(relevant_chunks)}개")
        
        if not relevant_chunks:
            return {
                "answer": "해당 문서에서 관련 내용을 찾을 수 없습니다.",
                "sources": [],
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
        
        # Step 3: Reasoner - 답변 생성 (핵심!)
        print("\n[Step 3/5] Reasoner - 답변 생성")
        raw_answer = self._reasoner(question, relevant_chunks, doc_title, intent)
        print(f"  → 답변 생성 완료 ({len(raw_answer)}자)")
        
        # Step 4: Synthesizer - 답변 정리
        print("\n[Step 4/5] Synthesizer - 답변 정리")
        formatted_answer = self._synthesizer(raw_answer, doc_title)
        
        # Step 5: Guardrail - 민감정보 체크
        print("\n[Step 5/5] Guardrail - 안전성 검증")
        final_answer, is_safe = self._guardrail(formatted_answer)
        print(f"  → 안전성: {'통과' if is_safe else '마스킹 적용'}")
        
        # 처리 시간 계산
        processing_time = int((time.time() - start_time) * 1000)
        
        # 비용 로그 기록
        self._log_cost(doc_id, user_id, processing_time)
        
        result = {
            "answer": final_answer,
            "sources": [chunk[:100] + "..." for chunk in relevant_chunks[:3]],
            "doc_title": doc_title,
            "intent": intent,
            "processing_time_ms": processing_time,
            "models_used": {
                "router": "gemini-2.0-flash",
                "researcher": "gemini-2.0-flash",
                "reasoner": "gpt-4o-mini",
                "synthesizer": "gemini-2.0-flash",
                "guardrail": "gemini-2.0-flash"
            }
        }
        
        print(f"\n[DocChat] 완료! ({processing_time}ms)")
        
        return result
    
    # ==================== Step 1: Router ====================
    
    def _router(self, question: str) -> str:
        """
        질문 의도 파악 (Gemini Flash)
        - query: 단순 질문
        - summary: 요약 요청
        - analysis: 분석 요청
        - search: 특정 내용 찾기
        """
        if self.use_mock:
            return self._mock_router(question)
        
        prompt = f"""다음 질문의 의도를 분류해주세요.

질문: {question}

다음 중 하나만 답해주세요 (다른 텍스트 없이):
- query: 단순 질문/정보 요청
- summary: 요약 요청
- analysis: 분석/비교 요청
- search: 특정 내용 찾기
"""
        
        try:
            response = self.gemini_model.generate_content(
                prompt,
                generation_config={"temperature": 0.1, "max_output_tokens": 10}
            )
            intent = response.text.strip().lower()
            
            if intent not in ["query", "summary", "analysis", "search"]:
                intent = "query"
            
            return intent
            
        except Exception as e:
            print(f"  ⚠️ Router 오류: {e}")
            return "query"
    
    def _mock_router(self, question: str) -> str:
        """Mock Router"""
        q_lower = question.lower()
        
        if "요약" in q_lower or "정리" in q_lower:
            return "summary"
        elif "분석" in q_lower or "비교" in q_lower:
            return "analysis"
        elif "찾아" in q_lower or "어디" in q_lower:
            return "search"
        else:
            return "query"
    
    # ==================== Step 2: Researcher ====================
    
    def _researcher(self, doc_id: str, question: str) -> List[str]:
        """
        해당 문서에서 관련 청크 검색 (Gemini Flash 임베딩 + Milvus)
        """
        try:
            # 해당 문서의 모든 청크 가져오기
            from core.embedding import EmbeddingGenerator
            
            embedding_gen = EmbeddingGenerator()
            question_embedding = embedding_gen.create(question)
            
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
            print(f"  ⚠️ Researcher 오류: {e}")
            # Fallback: PostgreSQL에서 문서 내용 직접 가져오기
            return self._fallback_get_chunks(doc_id)
    
    def _fallback_get_chunks(self, doc_id: str) -> List[str]:
        """Fallback: Milvus에서 doc_id로 청크 직접 조회"""
        try:
            results = self.milvus_client.get_chunks_by_doc_id(doc_id)
            return [r.get("chunk_text", "") for r in results if r.get("chunk_text")]
        except Exception:
            return []
    
    # ==================== Step 3: Reasoner ====================
    
    def _reasoner(
        self,
        question: str,
        chunks: List[str],
        doc_title: str,
        intent: str
    ) -> str:
        """
        답변 생성 (GPT-4o-mini) - 핵심!
        """
        if self.use_mock:
            return self._mock_reasoner(question, chunks, doc_title)
        
        # 청크들을 컨텍스트로 결합
        context = "\n\n---\n\n".join(chunks)
        
        # 의도별 프롬프트 조정
        intent_instruction = {
            "query": "질문에 대해 명확하게 답변해주세요.",
            "summary": "문서 내용을 간결하게 요약해주세요.",
            "analysis": "문서 내용을 분석하여 인사이트를 제공해주세요.",
            "search": "관련 내용을 찾아 설명해주세요."
        }
        
        prompt = f"""당신은 '{doc_title}' 문서에 대해 답변하는 AI 어시스턴트입니다.

## 문서 내용:
{context}

## 사용자 질문:
{question}

## 지시사항:
{intent_instruction.get(intent, intent_instruction["query"])}

문서에 없는 내용은 추측하지 말고, 문서 기반으로만 답변해주세요.
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "문서 기반 QA 어시스턴트입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"  ⚠️ Reasoner 오류: {e}")
            return self._mock_reasoner(question, chunks, doc_title)
    
    def _mock_reasoner(self, question: str, chunks: List[str], doc_title: str) -> str:
        """Mock Reasoner"""
        if not chunks:
            return "해당 문서에서 관련 내용을 찾을 수 없습니다."
        
        return f"""'{doc_title}' 문서를 기반으로 답변드립니다.

{chunks[0][:500]}...

(Mock 모드: 실제 LLM 연동 시 더 정확한 답변이 생성됩니다)"""
    
    # ==================== Step 4: Synthesizer ====================
    
    def _synthesizer(self, raw_answer: str, doc_title: str) -> str:
        """
        답변 정리 및 포맷팅 (Gemini Flash)
        """
        if self.use_mock:
            return raw_answer
        
        prompt = f"""다음 답변을 읽기 좋게 정리해주세요.
불필요한 내용은 제거하고, 핵심만 남겨주세요.
마크다운 형식으로 정리해주세요.

원본 답변:
{raw_answer}

정리된 답변:"""
        
        try:
            response = self.gemini_model.generate_content(
                prompt,
                generation_config={"temperature": 0.2, "max_output_tokens": 1000}
            )
            
            return response.text.strip()
            
        except Exception as e:
            print(f"  ⚠️ Synthesizer 오류: {e}")
            return raw_answer
    
    # ==================== Step 5: Guardrail ====================
    
    def _guardrail(self, answer: str) -> tuple:
        """
        민감정보 체크 및 마스킹 (Gemini Flash)
        """
        import re
        
        is_safe = True
        masked_answer = answer
        
        # 전화번호 마스킹
        phone_pattern = r'01[0-9]-?\d{3,4}-?\d{4}'
        if re.search(phone_pattern, masked_answer):
            masked_answer = re.sub(phone_pattern, '[전화번호 마스킹]', masked_answer)
            is_safe = False
        
        # 주민번호 마스킹
        ssn_pattern = r'\d{6}-?[1-4]\d{6}'
        if re.search(ssn_pattern, masked_answer):
            masked_answer = re.sub(ssn_pattern, '[주민번호 마스킹]', masked_answer)
            is_safe = False
        
        # 이메일 마스킹
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        if re.search(email_pattern, masked_answer):
            masked_answer = re.sub(email_pattern, '[이메일 마스킹]', masked_answer)
            is_safe = False
        
        return masked_answer, is_safe
    
    # ==================== 비용 로깅 ====================
    
    def _log_cost(self, doc_id: str, user_id: str, processing_time: int):
        """비용 로그 기록"""
        try:
            # user_id가 없으면 스킵
            if not user_id or user_id == "anonymous":
                return
            
            # 예상 토큰 (간단 추정)
            estimated_tokens = 2500  # 입력 + 출력
            
            # 비용 계산 (대략)
            # Gemini Flash: $0.075/1M input, $0.30/1M output
            # GPT-4o-mini: $0.15/1M input, $0.60/1M output
            estimated_cost_usd = 0.0012
            estimated_cost_krw = estimated_cost_usd * 1400
            
            self.postgres_client.log_cost(
                user_id=user_id,
                doc_id=doc_id,
                operation="doc_chat",
                tokens_used=estimated_tokens,
                cost_usd=estimated_cost_usd,
                cost_krw=estimated_cost_krw,
                model_name="doc_chat_pipeline"
            )
        except Exception as e:
            print(f"  ⚠️ 비용 로그 실패: {e}")
    
    def close(self):
        """리소스 정리"""
        self.postgres_client.close()
        self.milvus_client.close()
        print("[DocChat] 연결 종료")


# ==================== 테스트 코드 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("문서별 채팅 테스트 (5단계 SLM 파이프라인)")
    print("=" * 60)
    
    try:
        chat = DocumentChat()
        
        # 테스트용 문서 ID 조회
        docs = chat.postgres_client.list_documents(limit=1)
        
        if not docs:
            print("❌ 테스트할 문서가 없습니다. 먼저 문서를 업로드하세요.")
        else:
            doc_id = docs[0]["doc_id"]
            doc_title = docs[0]["title"]
            
            print(f"\n테스트 문서: {doc_title} ({doc_id})")
            
            # 테스트 질문
            questions = [
                "이 문서의 핵심 내용이 뭐야?",
                "이 문서를 요약해줘",
            ]
            
            for q in questions:
                print(f"\n{'='*60}")
                print(f"질문: {q}")
                print("=" * 60)
                
                result = chat.chat(doc_id=doc_id, question=q)
                
                print(f"\n📝 답변:")
                print(result.get("answer", "답변 없음"))
                print(f"\n⏱️ 처리 시간: {result.get('processing_time_ms', 0)}ms")
        
        chat.close()
        
        print("\n" + "=" * 60)
        print("✓ 테스트 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()