"""
AI-agent Core Pipeline
5단계 레이어드 파이프라인: Router → Researcher → Reasoner → Synthesizer → Guardrail
"""

from typing import Dict, Any, Optional, Literal
from enum import Enum
import os
import time
import sys
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logger import get_logger
from core.cost_calculator import get_cost_calculator

# 환경 변수 로드
load_dotenv()


class ComplexityLevel(Enum):
    """요청 복잡도 레벨"""
    SIMPLE = "simple"      # 단순 조회 - Gemini Flash
    COMPLEX = "complex"    # 정밀 분석 - GPT-5, Claude 4.5 등
    BULK = "bulk"          # 대량 문서 분석 - 병렬 처리


class IntentType(Enum):
    """사용자 의도 분류"""
    QUERY = "query"              # 단순 질의
    ANALYSIS = "analysis"        # 분석 요청
    GENERATION = "generation"    # 생성 요청
    SEARCH = "search"            # 검색 요청


# ==================== Step 1: Router ====================
class Router:
    """
    의도 분류 및 복잡도 판단
    - 사용자 요청의 의도를 파악
    - 복잡도에 따라 적절한 LLM 선택
    """
    
    def __init__(self):
        self.model = "gemini/gemini-2.0-flash-exp"  # 빠른 의도 분류용 (0.72초)
        
        # 의도별 키워드 사전 (확장)
        self.intent_keywords = {
            IntentType.SEARCH: [
                "검색", "찾아", "찾기", "어디", "조회", "확인",
                "알려줘", "보여줘", "있어", "있나요", "찾아줘"
            ],
            IntentType.ANALYSIS: [
                "분석", "비교", "평가", "검토", "조사", "연구",
                "파악", "추세", "경향", "통계", "데이터", "인사이트",
                "어떻게", "왜", "이유", "원인", "결과", "영향"
            ],
            IntentType.GENERATION: [
                "생성", "만들어", "작성", "제작", "개발", "구현",
                "설계", "기획", "초안", "문서", "보고서", "제안서",
                "코드", "프로그램", "시스템"
            ]
        }
        
        # 복잡도 판단 키워드
        self.complexity_keywords = {
            "high": [
                "상세", "자세히", "깊이", "심층", "종합", "전체",
                "모든", "전반", "다각도", "다양한", "복합", "통합"
            ],
            "low": [
                "간단히", "요약", "개요", "핵심", "주요", "빠르게",
                "짧게", "간략히"
            ]
        }
    
    def calculate_confidence(self, user_input: str, intent: IntentType) -> float:
        """
        키워드 기반 분류의 신뢰도 계산
        
        Returns:
            0.0 ~ 1.0 사이의 신뢰도 점수
        """
        user_input_lower = user_input.lower()
        
        # 해당 의도의 키워드 매칭 개수
        matched_keywords = 0
        if intent in self.intent_keywords:
            for keyword in self.intent_keywords[intent]:
                if keyword in user_input_lower:
                    matched_keywords += 1
        
        # 다른 의도의 키워드 매칭 개수
        other_matches = 0
        for other_intent, keywords in self.intent_keywords.items():
            if other_intent != intent:
                for keyword in keywords:
                    if keyword in user_input_lower:
                        other_matches += 1
        
        # 신뢰도 계산
        if matched_keywords == 0:
            return 0.3  # 키워드 매칭 없음 (기본값 QUERY)
        
        total_matches = matched_keywords + other_matches
        if total_matches == 0:
            return 0.5
        
        # 매칭 비율 기반 신뢰도
        confidence = matched_keywords / (matched_keywords + other_matches * 0.5)
        
        # 입력 길이에 따른 보정 (짧은 입력은 신뢰도 낮춤)
        if len(user_input) < 20:
            confidence *= 0.8
        
        return min(confidence, 1.0)
    
    def classify_intent_with_llm(self, user_input: str) -> IntentType:
        """
        LLM을 사용한 의도 분류 (신뢰도가 낮을 때만 사용)
        
        Note:
            실제 API 연동 전까지는 키워드 기반 결과 반환
        """
        # TODO: 실제 LLM API 연동
        # prompt = f'''다음 사용자 요청의 의도를 정확히 하나만 선택하세요:
        # "{user_input}"
        # 
        # 선택지:
        # - QUERY: 단순 질문이나 정보 요청
        # - SEARCH: 특정 정보나 문서 검색
        # - ANALYSIS: 데이터 분석, 비교, 평가
        # - GENERATION: 문서나 콘텐츠 생성
        # 
        # 답변은 위 4가지 중 하나만 출력하세요.'''
        # 
        # try:
        #     response = litellm.completion(
        #         model=self.model,
        #         messages=[{"role": "user", "content": prompt}],
        #         temperature=0.1
        #     )
        #     result = response.choices[0].message.content.strip().upper()
        #     
        #     # 결과 매핑
        #     intent_map = {
        #         "QUERY": IntentType.QUERY,
        #         "SEARCH": IntentType.SEARCH,
        #         "ANALYSIS": IntentType.ANALYSIS,
        #         "GENERATION": IntentType.GENERATION
        #     }
        #     return intent_map.get(result, IntentType.QUERY)
        # except:
        #     # LLM 실패 시 키워드 기반으로 폴백
        #     return self.classify_intent_keyword(user_input)
        
        # 임시: API 연동 전까지는 키워드 기반 사용
        print("  [LLM 분류 모드] API 연동 대기 중, 키워드 기반 사용")
        return self.classify_intent_keyword(user_input)
    
    def classify_intent_keyword(self, user_input: str) -> IntentType:
        """
        키워드 기반 의도 분류 (기존 로직)
        """
        user_input_lower = user_input.lower()
        scores = {intent: 0 for intent in IntentType}
        
        # 각 의도별 키워드 매칭 점수 계산
        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword in user_input_lower:
                    scores[intent] += 1
        
        # 점수가 가장 높은 의도 선택
        max_score = max(scores.values())
        
        if max_score == 0:
            # 키워드가 없으면 기본값
            return IntentType.QUERY
        
        # 동점인 경우 우선순위: ANALYSIS > GENERATION > SEARCH > QUERY
        priority = [IntentType.ANALYSIS, IntentType.GENERATION, IntentType.SEARCH, IntentType.QUERY]
        for intent in priority:
            if scores[intent] == max_score:
                return intent
        
        return IntentType.QUERY
    
    def classify_intent(self, user_input: str) -> IntentType:
        """
        하이브리드 의도 분류
        - 1차: 키워드 기반 분류
        - 신뢰도 < 0.7: LLM 기반 분류 (비용 절감)
        """
        # 1차: 키워드 기반 분류
        keyword_intent = self.classify_intent_keyword(user_input)
        
        # 신뢰도 계산
        confidence = self.calculate_confidence(user_input, keyword_intent)
        
        # 신뢰도가 높으면 키워드 결과 사용
        if confidence >= 0.7:
            print(f"  [키워드 분류] 신뢰도: {confidence:.2f}")
            return keyword_intent
        
        # 신뢰도가 낮으면 LLM 사용
        print(f"  [키워드 분류] 신뢰도 낮음: {confidence:.2f}, LLM으로 재분류")
        return self.classify_intent_with_llm(user_input)
    
    def determine_complexity(self, user_input: str, intent: IntentType) -> ComplexityLevel:
        """
        복잡도 판단 (개선된 버전)
        - 다차원 분석: 길이, 의도, 키워드, 구조
        """
        user_input_lower = user_input.lower()
        
        # 1. 길이 기반 점수 (0-4점)
        input_length = len(user_input)
        if input_length > 500:
            length_score = 4
        elif input_length > 300:
            length_score = 3
        elif input_length > 150:
            length_score = 2
        elif input_length > 80:
            length_score = 1
        else:
            length_score = 0
        
        # 2. 의도 기반 점수 (0-2점)
        intent_score = 0
        if intent == IntentType.ANALYSIS:
            intent_score = 2
        elif intent == IntentType.GENERATION:
            intent_score = 1
        
        # 3. 복잡도 키워드 점수 (-2 ~ +3점)
        keyword_score = 0
        for keyword in self.complexity_keywords["high"]:
            if keyword in user_input_lower:
                keyword_score += 1
        for keyword in self.complexity_keywords["low"]:
            if keyword in user_input_lower:
                keyword_score -= 1
        
        # 4. 구조 복잡도 점수 (0-3점)
        structure_score = 0
        
        # 문장 개수 (마침표, 물음표 기준)
        sentence_count = user_input.count(".") + user_input.count("。") + \
                        user_input.count("?") + user_input.count("？") + \
                        user_input.count("!") + user_input.count("！")
        if sentence_count > 5:
            structure_score += 2
        elif sentence_count > 3:
            structure_score += 1
        
        # 질문이 여러 개인 경우
        question_marks = user_input.count("?") + user_input.count("？")
        if question_marks > 2:
            structure_score += 1
        
        # 조건문이 있는 경우
        if any(word in user_input_lower for word in ["만약", "경우", "조건", "if", "when"]):
            structure_score += 1
        
        # 총점 계산
        total_score = length_score + intent_score + keyword_score + structure_score
        
        # 복잡도 결정 (임계값 조정)
        if total_score >= 7:
            return ComplexityLevel.BULK
        elif total_score >= 3:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.SIMPLE
    
    def route(self, user_input: str) -> Dict[str, Any]:
        """라우팅 실행"""
        intent = self.classify_intent(user_input)
        complexity = self.determine_complexity(user_input, intent)
        
        return {
            "intent": intent.value,
            "complexity": complexity.value,
            "user_input": user_input
        }


# ==================== Step 2: Researcher ====================
class Researcher:
    """
    RAG 기반 문서 검색 및 정보 인출
    - AI Drive에서 관련 문서 검색
    - 벡터 검색을 통한 유사도 기반 정보 추출
    """
    
    def __init__(self, use_rag: bool = False):
        """
        Args:
            use_rag: RAG 시스템 사용 여부 (개발 중에는 False, 배포 시 True)
        """
        self.use_rag = use_rag
        self.embedding_model = "text-embedding-3-small"
        
        # RAG 사용 시에만 클라이언트 초기화
        if self.use_rag:
            try:
                # AI Drive 모듈 import (Feature-H 브랜치의 코드)
                from services.ai_drive.db.milvus_client import MilvusClient
                from services.ai_drive.core.embedding import EmbeddingGenerator
                
                self.milvus_client = MilvusClient()
                self.embedding_generator = EmbeddingGenerator()
                print("  [RAG] AI Drive 연동 활성화")
            except ImportError as e:
                print(f"  [RAG] AI Drive 모듈을 찾을 수 없습니다: {e}")
                print("  [RAG] Mock 검색 모드로 전환")
                self.use_rag = False
            except Exception as e:
                print(f"  [RAG] 초기화 실패: {e}")
                print("  [RAG] Mock 검색 모드로 전환")
                self.use_rag = False
        else:
            print("  [RAG] Mock 검색 모드 (use_rag=False)")
    
    def search_documents(self, query: str, top_k: int = 5, department: str = "개발팀") -> list[Dict[str, Any]]:
        """
        문서 검색 (RAG 또는 Mock)
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 문서 개수
            department: 사용자 부서 (권한 필터링용)
            
        Returns:
            검색된 문서 리스트
        """
        if self.use_rag:
            return self._search_with_rag(query, top_k, department)
        else:
            return self._search_mock(query, top_k)
    
    def _search_with_rag(self, query: str, top_k: int, department: str) -> list[Dict[str, Any]]:
        """
        실제 RAG 검색 (AI Drive 연동)
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 문서 개수
            department: 사용자 부서
            
        Returns:
            검색된 문서 리스트
        """
        try:
            # 1. 쿼리를 임베딩으로 변환
            query_embedding = self.embedding_generator.create(query)
            
            # 2. Milvus에서 유사도 검색
            results = self.milvus_client.search(
                query_embedding=query_embedding,
                department=department,
                top_k=top_k,
                include_company=True  # 회사 전체 공개 문서도 포함
            )
            
            # 3. 결과 포맷 변환
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result.get("chunk_text", ""),
                    "score": result.get("score", 0.0),
                    "source": result.get("doc_id", "unknown"),
                    "doc_id": result.get("doc_id", ""),
                    "chunk_id": result.get("chunk_id", "")
                })
            
            print(f"  [RAG] 검색 완료: {len(formatted_results)}개 문서 발견")
            return formatted_results
            
        except Exception as e:
            print(f"  [RAG] 검색 실패: {e}")
            print("  [RAG] Mock 검색으로 폴백")
            return self._search_mock(query, top_k)
    
    def _search_mock(self, query: str, top_k: int) -> list[Dict[str, Any]]:
        """
        Mock 검색 (테스트용)
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 문서 개수
            
        Returns:
            Mock 문서 리스트
        """
        print(f"  [Mock] '{query}'에 대한 Mock 검색 실행")
        
        # Mock 데이터 생성
        mock_documents = [
            {
                "content": f"'{query}'와 관련된 Mock 문서 내용입니다. 이것은 테스트용 데이터로, 실제 RAG 연동 시 실제 문서 내용으로 대체됩니다.",
                "score": 0.95,
                "source": "mock_document_1.pdf",
                "doc_id": "mock-001",
                "chunk_id": "mock-chunk-001"
            },
            {
                "content": f"'{query}'에 대한 추가 정보입니다. 비용 최적화, 성능 개선 등의 내용이 포함될 수 있습니다.",
                "score": 0.87,
                "source": "mock_document_2.pdf",
                "doc_id": "mock-002",
                "chunk_id": "mock-chunk-002"
            }
        ]
        
        # top_k 개수만큼 반환
        return mock_documents[:top_k]
    
    def retrieve(self, routing_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        정보 검색 실행
        
        Args:
            routing_result: Router의 출력 결과
            
        Returns:
            검색 결과가 추가된 딕셔너리
        """
        user_input = routing_result["user_input"]
        intent = routing_result["intent"]
        complexity = routing_result["complexity"]
        
        # 검색이 필요한 경우에만 실행
        # - SEARCH, ANALYSIS 의도
        # - COMPLEX, BULK 복잡도
        should_search = (
            intent in ["search", "analysis"] or
            complexity in ["complex", "bulk"]
        )
        
        if should_search:
            print(f"  → 문서 검색 필요 (의도: {intent}, 복잡도: {complexity})")
            documents = self.search_documents(user_input, top_k=5)
        else:
            print(f"  → 문서 검색 스킵 (의도: {intent}, 복잡도: {complexity})")
            documents = []
        
        return {
            **routing_result,
            "retrieved_documents": documents
        }



# ==================== Step 3: Reasoner & Verification ====================
class Reasoner:
    """
    논리적 답변 생성 및 CoT(Chain of Thought) 기반 팩트체크
    - 복잡도에 따라 적절한 LLM 선택
    - 모델 실패 시 Fallback 메커니즘
    - 답변의 논리적 일관성 검증
    """
    
    def __init__(self):
        # 복잡도별 주 모델 매핑 (기획서 기준 최신 모델)
        self.model_mapping = {
            ComplexityLevel.SIMPLE.value: "gemini/gemini-2.0-flash-exp",
            ComplexityLevel.COMPLEX.value: "gpt-5",
            ComplexityLevel.BULK.value: "claude-4-sonnet"
        }
        
        # 복잡도별 Fallback 모델 우선순위 (다양한 후보군)
        self.fallback_models = {
            # SIMPLE: 초고속 응답 + 저비용 우선
            ComplexityLevel.SIMPLE.value: [
                "gemini/gemini-2.0-flash-exp",      # 주력: 0.72초 초고속
                "gpt-4o-mini",                       # 대체1: OpenAI 경량
                "claude-3-haiku",                    # 대체2: Anthropic 경량
                "meta-llama/llama-4-8b",            # 대체3: 오픈소스 경량
            ],
            # COMPLEX: 정밀 분석 + 고품질 추론
            ComplexityLevel.COMPLEX.value: [
                "gpt-5",                             # 주력: 최신 GPT
                "claude-4-sonnet",                   # 대체1: Claude 최신
                "gemini/gemini-2.0-pro-exp",        # 대체2: Gemini Pro
                "openai/o1",                         # 대체3: 사고 체인 특화
                "meta-llama/llama-4-70b",           # 대체4: 오픈소스 대형
            ],
            # BULK: 대량 처리 + 병렬 최적화
            ComplexityLevel.BULK.value: [
                "claude-4-sonnet",                   # 주력: 긴 컨텍스트 처리
                "gpt-5",                             # 대체1: GPT 최신
                "gemini/gemini-2.0-pro-exp",        # 대체2: Gemini Pro
                "meta-llama/llama-4-70b",           # 대체3: 오픈소스 대형
            ]
        }
        
        self.max_retries = 3
    
    def select_model(self, complexity: str) -> str:
        """복잡도에 따른 모델 선택"""
        return self.model_mapping.get(complexity, "gemini-2.0-flash")
    
    def generate_response_with_fallback(self, context: Dict[str, Any]) -> tuple[str, str]:
        """Fallback 메커니즘을 포함한 답변 생성"""
        complexity = context["complexity"]
        user_input = context["user_input"]
        documents = context.get("retrieved_documents", [])
        
        # Fallback 모델 리스트 가져오기
        models_to_try = self.fallback_models.get(complexity, ["gemini-2.0-flash"])
        
        last_error = None
        for model in models_to_try:
            try:
                # TODO: 실제 LLM 호출 구현 (litellm 사용)
                # response = litellm.completion(
                #     model=model,
                #     messages=[{"role": "user", "content": user_input}]
                # )
                # return response.choices[0].message.content, model
                
                # 임시 응답 (실제 구현 시 위 코드로 대체)
                print(f"  → 모델 시도: {model}")
                response = f"[{model}] {user_input}에 대한 답변입니다."
                return response, model
                
            except Exception as e:
                last_error = e
                print(f"  [!] 모델 {model} 실패: {str(e)}")
                continue
        
        # 모든 모델 실패 시
        raise Exception(f"모든 Fallback 모델 실패. 마지막 오류: {last_error}")
    
    def generate_response(self, context: Dict[str, Any]) -> tuple[str, str]:
        """답변 생성 (Fallback 포함)"""
        return self.generate_response_with_fallback(context)
    
    def verify(self, response: str, model_used: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """팩트체크 및 검증"""
        # TODO: CoT 기반 검증 로직 구현
        is_verified = True
        confidence_score = 0.95
        
        return {
            **context,
            "response": response,
            "model_used": model_used,
            "verified": is_verified,
            "confidence": confidence_score
        }
    
    def reason(self, research_result: Dict[str, Any]) -> Dict[str, Any]:
        """추론 실행"""
        response, model_used = self.generate_response(research_result)
        return self.verify(response, model_used, research_result)


# ==================== Step 4: Synthesizer ====================
class Synthesizer:
    """
    표준 레이아웃 적용 및 최종 렌더링
    - 응답을 사용자 친화적인 형식으로 변환
    - 마크다운, HTML 등 다양한 포맷 지원
    """
    
    def format_response(self, reasoning_result: Dict[str, Any]) -> str:
        """응답 포맷팅"""
        response = reasoning_result["response"]
        confidence = reasoning_result["confidence"]
        
        # 마크다운 형식으로 포맷팅
        formatted = f"""
## 답변

{response}

---
**신뢰도**: {confidence * 100:.1f}%
**모델**: {reasoning_result.get('complexity', 'unknown')}
"""
        return formatted.strip()
    
    def synthesize(self, reasoning_result: Dict[str, Any]) -> Dict[str, Any]:
        """최종 합성"""
        formatted_response = self.format_response(reasoning_result)
        
        return {
            **reasoning_result,
            "formatted_response": formatted_response
        }


# ==================== Step 5: Guardrail ====================
class Guardrail:
    """
    개인정보 마스킹 및 최종 안전 검증
    - 민감 정보 필터링
    - 유해 콘텐츠 차단
    - 복잡한 작업의 품질 검수 (COMPLEX, BULK)
    """
    
    def __init__(self):
        self.sensitive_patterns = [
            r'\d{3}-\d{4}-\d{4}',  # 전화번호
            r'\d{6}-\d{7}',        # 주민등록번호
        ]
        self.quality_check_model = "gemini/gemini-2.0-flash-exp"  # 빠른 검수용
    
    def mask_sensitive_info(self, text: str) -> str:
        """민감 정보 마스킹"""
        import re
        masked_text = text
        
        # 전화번호 마스킹
        masked_text = re.sub(r'(\d{3})-(\d{4})-(\d{4})', r'\1-****-\3', masked_text)
        # 주민등록번호 마스킹
        masked_text = re.sub(r'(\d{6})-(\d{7})', r'\1-*******', masked_text)
        
        return masked_text
    
    def check_safety(self, text: str) -> bool:
        """안전성 검사"""
        # TODO: 유해 콘텐츠 검사 로직 구현
        return True
    
    def verify_quality(self, synthesis_result: Dict[str, Any]) -> Dict[str, Any]:
        """품질 검수 (복잡한 작업에 대해서만 수행)"""
        complexity = synthesis_result.get("complexity")
        
        # SIMPLE 작업은 품질 검수 스킵
        if complexity == ComplexityLevel.SIMPLE.value:
            return {
                "quality_verified": True,
                "quality_score": 1.0,
                "quality_issues": [],
                "needs_regeneration": False
            }
        
        # COMPLEX, BULK 작업은 품질 검수 수행
        print("  → 품질 검수 수행 중...")
        
        user_input = synthesis_result.get("user_input", "")
        response = synthesis_result.get("response", "")
        intent = synthesis_result.get("intent", "")
        
        quality_issues = []
        
        # 1. 요청사항 충족도 검증
        if not self._check_completeness(user_input, response, intent):
            quality_issues.append("요청사항이 완전히 충족되지 않았습니다.")
        
        # 2. 논리적 일관성 검증
        if not self._check_logical_consistency(response):
            quality_issues.append("논리적 일관성이 부족합니다.")
        
        # 3. 누락된 정보 확인
        missing_info = self._check_missing_information(user_input, response, intent)
        if missing_info:
            quality_issues.extend(missing_info)
        
        # 품질 점수 계산 (이슈 개수에 따라)
        quality_score = max(0.0, 1.0 - (len(quality_issues) * 0.2))
        
        # 재생성 필요 여부 (품질 점수 0.6 미만)
        needs_regeneration = quality_score < 0.6
        
        if quality_issues:
            print(f"  [!] 품질 이슈 발견: {len(quality_issues)}개")
            for issue in quality_issues:
                print(f"     - {issue}")
        else:
            print("  [OK] 품질 검수 통과")
        
        return {
            "quality_verified": len(quality_issues) == 0,
            "quality_score": quality_score,
            "quality_issues": quality_issues,
            "needs_regeneration": needs_regeneration
        }
    
    def _check_completeness(self, user_input: str, response: str, intent: str) -> bool:
        """요청사항 충족도 검증"""
        # TODO: LLM을 사용한 정교한 검증 구현
        # 현재는 간단한 길이 기반 체크
        if intent == IntentType.ANALYSIS.value:
            return len(response) > 100  # 분석은 충분한 길이 필요
        elif intent == IntentType.GENERATION.value:
            return len(response) > 50   # 생성도 최소 길이 필요
        return True
    
    def _check_logical_consistency(self, response: str) -> bool:
        """논리적 일관성 검증"""
        # TODO: LLM을 사용한 논리적 일관성 검증
        # 현재는 기본적인 체크만
        return len(response) > 0
    
    def _check_missing_information(self, user_input: str, response: str, intent: str) -> list[str]:
        """누락된 정보 확인"""
        # TODO: LLM을 사용한 누락 정보 탐지
        missing = []
        
        # 분석 요청인데 데이터나 근거가 없는 경우
        if intent == IntentType.ANALYSIS.value:
            if "데이터" not in response and "근거" not in response:
                missing.append("분석 근거나 데이터가 누락되었습니다.")
        
        return missing
    
    def guard(self, synthesis_result: Dict[str, Any]) -> Dict[str, Any]:
        """가드레일 실행"""
        formatted_response = synthesis_result["formatted_response"]
        
        # 1. 품질 검수 (복잡한 작업에 대해)
        quality_result = self.verify_quality(synthesis_result)
        
        # 2. 민감 정보 마스킹
        safe_response = self.mask_sensitive_info(formatted_response)
        
        # 3. 안전성 검사
        is_safe = self.check_safety(safe_response)
        
        # 재생성 필요 시 경고 메시지 추가
        if quality_result["needs_regeneration"]:
            safe_response = f"""[!] 품질 검수 경고
다음 이슈가 발견되었습니다:
{chr(10).join(f'- {issue}' for issue in quality_result['quality_issues'])}

재생성을 권장합니다.

---

{safe_response}
"""
        
        return {
            **synthesis_result,
            **quality_result,
            "final_response": safe_response,
            "is_safe": is_safe
        }


# ==================== Main Pipeline ====================
class Pipeline:
    """
    5단계 파이프라인 오케스트레이터
    Router → Researcher → Reasoner → Synthesizer → Guardrail
    """
    
    def __init__(self, use_rag: bool = False):
        """
        Args:
            use_rag: RAG 시스템 사용 여부 (기본값: False)
        """
        self.router = Router()
        self.researcher = Researcher(use_rag=use_rag)  # RAG 플래그 전달
        self.reasoner = Reasoner()
        self.synthesizer = Synthesizer()
        self.guardrail = Guardrail()
        self.logger = get_logger()
        self.cost_calculator = get_cost_calculator()
    
    def process(self, user_input: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """전체 파이프라인 실행"""
        print(f"[Pipeline] 처리 시작: {user_input[:50]}...")
        
        # 세션 시작
        session_id = self.logger.start_session(user_input, user_id)
        
        try:
            # Step 1: Router
            print("[Step 1/5] Router - 의도 분류 및 복잡도 판단")
            step_start = time.time()
            routing_result = self.router.route(user_input)
            step_duration = (time.time() - step_start) * 1000
            self.logger.log_step("Router", routing_result, step_duration)
            
            # Step 2: Researcher
            print("[Step 2/5] Researcher - RAG 기반 문서 검색")
            step_start = time.time()
            research_result = self.researcher.retrieve(routing_result)
            step_duration = (time.time() - step_start) * 1000
            self.logger.log_step("Researcher", {
                "documents_found": len(research_result.get("retrieved_documents", []))
            }, step_duration)
            
            # Step 3: Reasoner
            print("[Step 3/5] Reasoner - 논리적 답변 생성 및 검증")
            step_start = time.time()
            reasoning_result = self.reasoner.reason(research_result)
            step_duration = (time.time() - step_start) * 1000
            self.logger.log_step("Reasoner", {
                "model_used": reasoning_result.get("model_used"),
                "verified": reasoning_result.get("verified"),
                "confidence": reasoning_result.get("confidence")
            }, step_duration)
            
            # 모델 사용 로깅 및 비용 계산
            # TODO: 실제 API 연동 시 litellm에서 토큰 수 가져오기
            # 현재는 예상 토큰 수로 계산
            estimated_input_tokens = len(user_input.split()) * 2  # 대략적인 추정
            estimated_output_tokens = len(reasoning_result.get("response", "").split()) * 2
            
            # 비용 계산
            cost_info = self.cost_calculator.calculate_cost(
                model_name=reasoning_result.get("model_used", "unknown"),
                input_tokens=estimated_input_tokens,
                output_tokens=estimated_output_tokens
            )
            
            # 로그에 비용 정보 기록
            self.logger.log_model_usage(
                model_name=reasoning_result.get("model_used", "unknown"),
                input_tokens=estimated_input_tokens,
                output_tokens=estimated_output_tokens,
                cost_info=cost_info
            )
            
            # Step 4: Synthesizer
            print("[Step 4/5] Synthesizer - 최종 렌더링")
            step_start = time.time()
            synthesis_result = self.synthesizer.synthesize(reasoning_result)
            step_duration = (time.time() - step_start) * 1000
            self.logger.log_step("Synthesizer", {}, step_duration)
            
            # Step 5: Guardrail
            print("[Step 5/5] Guardrail - 안전성 검증")
            step_start = time.time()
            final_result = self.guardrail.guard(synthesis_result)
            step_duration = (time.time() - step_start) * 1000
            self.logger.log_step("Guardrail", {
                "quality_verified": final_result.get("quality_verified"),
                "quality_score": final_result.get("quality_score"),
                "is_safe": final_result.get("is_safe")
            }, step_duration)
            
            print("[Pipeline] 처리 완료\n")
            
            # 세션 종료 (성공)
            self.logger.end_session(final_result, success=True)
            
            return final_result
            
        except Exception as e:
            # 에러 로깅
            self.logger.log_error(
                error_type=type(e).__name__,
                error_message=str(e),
                step_name="Pipeline"
            )
            
            # 세션 종료 (실패)
            self.logger.end_session({"error": str(e)}, success=False)
            
            raise


# ==================== 테스트 코드 ====================
if __name__ == "__main__":
    # 파이프라인 초기화
    pipeline = Pipeline()
    
    # 테스트 케이스
    test_inputs = [
        "AI 에이전트가 뭐야?",
        "최근 프로젝트 문서에서 비용 최적화 관련 내용을 분석해줘",
        "새로운 기능 명세서를 생성해줘"
    ]
    
    for test_input in test_inputs:
        print("=" * 80)
        result = pipeline.process(test_input)
        print("\n[최종 결과]")
        print(result["final_response"])
        print("\n")
