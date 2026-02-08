"""
오케스트레이터 인터페이스 (앱 레이어)
-----------------------------
이 모듈은 서비스 레이어 오케스트레이터의 프록시/래퍼 역할을 합니다.
모든 비즈니스 로직을 `services.orchestrator.pipeline`에 위임합니다.
"""


from typing import Dict, List, Optional
# Import the Real Brain (Directly Pipeline)
from services.orchestrator.pipeline import Pipeline

class Orchestrator:
    def __init__(self):
        # Initialize the Service Layer instance (Pipeline)
        self.pipeline = Pipeline()

    async def process(self, user_input: str, user_id: str, context_id: str = None, model_type: str = "AUTO", use_rag: bool = False) -> Dict:
        """
        서비스 계층으로 처리를 위임합니다.
        필요한 경우 웹 계층에서의 유효성 검사를 여기에 추가할 수 있습니다.
        """
        # RAG 사용 여부 업데이트
        self.pipeline.researcher.use_rag = use_rag
        return self.pipeline.process(user_input, user_id=user_id)

    async def analyze_for_draft(self, messages: List[Dict], template_schema: Dict) -> Dict:
        """
        초안 생성을 위한 분석 작업을 서비스 계층으로 위임합니다.
        """
        return await self.pipeline.analyze_for_draft(messages, template_schema)

    async def vectorize_agent(self, agent_data: Dict) -> bool:
        """
        에이전트 벡터화 작업을 서비스 계층으로 위임합니다.
        """
        return await self.pipeline.vectorize_agent(agent_data)

    async def recommend_agents(self, current_message: str, conversation_history: List[Dict] = None) -> Dict:
        """
        에이전트 추천을 위한 분석 작업을 서비스 계층으로 위임합니다.
        """
        return await self.pipeline.recommend_agents(current_message, conversation_history)

# Singleton Instance
orchestrator = Orchestrator()
