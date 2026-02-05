"""
Orchestrator Interface
----------------------
This module connects the web API layer to the AI Pipeline.
Integrates the 5-layer pipeline: Router → Researcher → Reasoner → Synthesizer → Guardrail
"""

from typing import Dict, List, Optional
import sys
from pathlib import Path

# Add project root to path to import core modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.pipeline import Pipeline

class Orchestrator:
    def __init__(self):
        """Initialize the Orchestrator with the AI Pipeline"""
        # Initialize pipeline with RAG disabled by default
        # RAG will be enabled per-request based on use_rag parameter
        self.pipeline_with_rag = None
        self.pipeline_without_rag = Pipeline(use_rag=False)
        print("[Orchestrator] Initialized with AI Pipeline")

    async def process(self, user_input: str, user_id: str, context_id: str = None, model_type: str = "AUTO", use_rag: bool = False) -> Dict:
        """
        Main entry point for processing user input.
        Executes the full 5-layer pipeline and returns the response.
        
        Args:
            user_input: User's question or request
            user_id: User identifier
            context_id: Optional conversation context ID
            model_type: Model selection (AUTO, GPT4, GEMINI, etc.)
            use_rag: Whether to use RAG (document search)
            
        Returns:
            Dictionary containing response, model used, and sources
        """
        print(f"[Orchestrator] Processing: {user_input[:50]}... (RAG: {use_rag})")
        
        # Select appropriate pipeline based on RAG flag
        if use_rag:
            # Lazy initialization of RAG pipeline
            if self.pipeline_with_rag is None:
                self.pipeline_with_rag = Pipeline(use_rag=True)
            pipeline = self.pipeline_with_rag
        else:
            pipeline = self.pipeline_without_rag
        
        # Execute the full pipeline
        result = pipeline.process(user_input=user_input, user_id=user_id)
        
        # Extract sources from retrieved documents
        sources = []
        if "retrieved_documents" in result:
            sources = [doc.get("source", "unknown") for doc in result["retrieved_documents"]]
        
        # Return in the format expected by the API
        return {
            "response": result.get("final_response", result.get("response", "No response generated")),
            "used_model": result.get("model_used", "unknown"),
            "sources": sources
        }

    async def recommend_agents(self, current_message: str, conversation_history: List[Dict] = None) -> Dict:
        """
        실시간 Agent 추천 (대화 중)
        현재 대화 내용을 분석하여 관련 Agent 2-3개 추천
        
        Args:
            current_message: 현재 입력 중인 메시지
            conversation_history: 이전 대화 내역 (선택)
            
        Returns:
            {
                "keywords": ["키워드1", "키워드2", ...],
                "category": "MARKETING",
                "topic": "주제 설명"
            }
        """
        # 대화 컨텍스트 구성
        if conversation_history:
            context = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in conversation_history[-5:]  # 최근 5개만
            ])
            full_text = f"{context}\nuser: {current_message}"
        else:
            full_text = current_message
        
        # 주제 분석 프롬프트
        prompt = f"""다음 대화의 주제와 의도를 분석해주세요:

{full_text}

다음 JSON 형식으로 답변해주세요:
{{
    "topic": "대화의 핵심 주제 (1문장)",
    "category": "MARKETING, CODING, HR, SALES, GENERAL 중 하나",
    "keywords": ["관련 키워드1", "키워드2", "키워드3"]
}}
"""
        
        # Pipeline으로 분석
        result = self.pipeline_without_rag.process(user_input=prompt, user_id=None)
        response_text = result.get("final_response", result.get("response", ""))
        
        # JSON 파싱
        try:
            import json
            import re
            
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return {
                    "topic": parsed.get("topic", "일반 대화"),
                    "category": parsed.get("category", "GENERAL"),
                    "keywords": parsed.get("keywords", [])
                }
        except Exception as e:
            print(f"[Orchestrator] Recommendation parsing failed: {e}")
        
        # 파싱 실패 시 기본값
        return {
            "topic": "일반 대화",
            "category": "GENERAL",
            "keywords": self._extract_simple_keywords(current_message)
        }
    
    def _extract_simple_keywords(self, text: str) -> List[str]:
        """
        간단한 키워드 추출 (파싱 실패 시 폴백)
        """
        # 간단한 단어 추출 (한글, 영문)
        import re
        words = re.findall(r'[가-힣a-zA-Z]{2,}', text)
        # 빈도수 기준 상위 3개
        from collections import Counter
        common = Counter(words).most_common(3)
        return [word for word, count in common]


    async def analyze_for_draft(self, messages: List[Dict]) -> Dict:
        """
        Agent 생성을 위한 대화 분석 (Pull-Fill 패턴)
        1. Agent Hub에서 템플릿 가져오기 (Pull)
        2. 대화 분석으로 템플릿 채우기 (Fill)
        
        NOTE: Push(Redis 저장)는 Service Layer에서 담당
        
        Args:
            messages: List of conversation messages
            
        Returns:
            채워진 Agent Draft 정보
        """
        # 1. PULL: Agent Hub에서 템플릿 가져오기
        template = self._get_agent_template()
        
        # 2. FILL: 대화 분석으로 템플릿 채우기
        filled_data = await self._analyze_conversation(messages, template)
        
        # 3. 템플릿과 분석 결과 병합
        draft_data = {**template, **filled_data}
        
        return draft_data
    
    def _get_agent_template(self) -> Dict:
        """
        Agent Hub에서 표준 템플릿 가져오기
        
        Returns:
            빈 Agent 템플릿
        """
        return {
            "name": "",
            "description": "",
            "category": "GENERAL",
            "system_prompt": "",
            "input_example": "",
            "output_example": "",
            "model_type": "AUTO",
            "use_rag": "False"
        }
    
    async def _analyze_conversation(self, messages: List[Dict], template: Dict) -> Dict:
        """
        대화 내용을 분석하여 템플릿 채우기
        
        Args:
            messages: 대화 내역
            template: 빈 템플릿
            
        Returns:
            채워진 필드들
        """
        # 대화 내용 결합
        conversation_text = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in messages
        ])
        
        # 구조화된 JSON 프롬프트
        prompt = f"""다음 대화 내용을 분석하여 AI 에이전트를 생성하기 위한 정보를 추출해주세요.

대화 내용:
{conversation_text}

다음 JSON 형식으로 답변해주세요:
{{
    "name": "에이전트 이름 (간단명료하게, 최대 50자)",
    "description": "에이전트의 역할과 목적 (1-2문장)",
    "system_prompt": "에이전트가 사용할 상세한 시스템 프롬프트",
    "input_example": "사용자 입력 예시",
    "output_example": "에이전트 출력 예시",
    "category": "MARKETING, CODING, HR, SALES, GENERAL 중 하나"
}}
"""
        
        # Pipeline으로 분석
        result = self.pipeline_without_rag.process(user_input=prompt, user_id=None)
        response_text = result.get("final_response", result.get("response", ""))
        
        # JSON 파싱 시도
        try:
            import json
            import re
            
            # JSON 부분 추출 (```json ... ``` 또는 { ... } 형태)
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                # 템플릿에 정의된 필드만 반환
                return {k: v for k, v in parsed.items() if k in template}
        except Exception as e:
            print(f"[Orchestrator] JSON parsing failed: {e}")
        
        # 파싱 실패 시 기본값
        return {
            "name": "Generated Agent",
            "description": "Auto-generated from conversation",
            "system_prompt": response_text[:500] if response_text else "You are a helpful assistant.",
            "input_example": "Help me with...",
            "output_example": "Here is the answer...",
            "category": "GENERAL"
        }

# Singleton Instance
orchestrator = Orchestrator()
