"""
오케스트레이터 인터페이스 (앱 레이어)
-----------------------------
이 모듈은 서비스 레이어 오케스트레이터의 프록시/래퍼 역할을 합니다.
모든 비즈니스 로직을 `services.orchestrator.pipeline`에 위임합니다.
"""


from typing import Dict, List, Optional
# Import the Real Brain (Directly Pipeline)
import time
from services.orchestrator.pipeline import Pipeline
from services.common.activity_logger import get_activity_logger
from services.ai_hub.db.agent_repo import AgentRepository
from application.database import get_db
from services.orchestrator.db.tables import ChatLog
class Orchestrator:
    def __init__(self):
        # Initialize the Service Layer instance (Pipeline)
        self.pipeline = Pipeline()
        self.activity_logger = get_activity_logger()

    async def process(self, user_input: str, user_id: str, context_id: str = None, model_type: str = "AUTO", use_rag: bool = False, agent_id: str = None) -> Dict:
        '''
        서비스 계층으로 처리를 위임합니다.
        
        Args:
            user_input: 사용자 입력
            user_id: 사용자 ID
            context_id: 대화 컨텍스트 ID
            model_type: "AUTO" 또는 프리미엄 모델 키 (GPT_5_2, GEMINI_3_PRO, PERPLEXITY, OPUS_4_6)
            use_rag: RAG 검색 사용 여부
        '''
        start = time.time()
        
        # RAG 사용 여부 업데이트
        self.pipeline.researcher.use_rag = use_rag
        
        # 모델 타입에 따라 분기
        # [Agent] 에이전트 정보 조회 및 시스템 프롬프트 로드
        system_prompt = None
        if agent_id:
            try:
                db_gen = get_db()
                db = next(db_gen)
                try:
                    agent_repo = AgentRepository()
                    agent = agent_repo.get_agent(db, agent_id)
                    
                    if agent:
                        system_prompt = agent.system_prompt
                        if model_type == "AUTO" and agent.model_type != "AUTO":
                            model_type = agent.model_type
                            
                        print(f"[Orchestrator] Agent Active: {agent.name} (Model: {model_type})")
                    else:
                        print(f"[Orchestrator] Warning: Agent {agent_id} not found.")
                finally:
                    db.close()
            except Exception as e:
                print(f"[Orchestrator] Failed to load agent context: {e}")

        # 모델 타입에 따라 분기
        if model_type == "AUTO":
            result = self.pipeline.process(
                user_input=user_input, 
                user_id=user_id,
                system_prompt=system_prompt  # [New] Inject Agent Persona
            )
        else:
            result = self.pipeline.process_premium(
                user_input=user_input,
                model_type=model_type,
                use_rag=use_rag,
                user_id=user_id,
                system_prompt=system_prompt  # [New] Inject Agent Persona
            )
        
        # 활동 로그
        duration_ms = int((time.time() - start) * 1000)
        self.activity_logger.log(
            user_id=user_id,
            action="chat",
            details={
                "model_type": model_type,
                "use_rag": use_rag,
                "intent": result.get("metadata", {}).get("intent", ""),
                "complexity": result.get("metadata", {}).get("complexity", ""),
            },
            success="error" not in result,
            duration_ms=duration_ms,
        )
        
        return result

    async def analyze_for_draft(self, messages: List[Dict], template_schema: Dict) -> Dict:
        """
        초안 생성을 위한 분석 작업을 서비스 계층으로 위임합니다.
        """
        return await self.pipeline.analyze_for_draft(messages, template_schema)

    async def recommend_agents(self, current_message: str, conversation_history: List[Dict] = None) -> Dict:
        """
        에이전트 추천을 위한 분석 작업을 서비스 계층으로 위임합니다.
        """
        return await self.pipeline.recommend_agents(current_message, conversation_history)

    def call_llm(self, task: str, prompt: str, options: dict = None) -> dict:
        """
        중앙 LLM 호출 프록시.
        서비스 계층의 Pipeline.call_llm()에 위임합니다.
        
        Args:
            task: TASK_MODEL_CONFIG의 키 (예: "tagging", "doc_chat")
            prompt: 사용자/작업 프롬프트
            options: 오버라이드 옵션 (선택)
            
        Returns:
            Pipeline.call_llm()의 반환값 dict
        """
        return self.pipeline.call_llm(task=task, prompt=prompt, options=options)

    def save_chat_log(self, user_id: str, session_id: str, user_input: str, ai_response: str, sources: Optional[List[Dict]] = None):
        """
        채팅 로그를 DB에 저장합니다. (Fire-and-forget 방식)
        """
        db = None
        try:
            db_gen = get_db()
            db = next(db_gen)
            log_entry = ChatLog(
                user_id=user_id,
                session_id=session_id,
                user_input=user_input,
                ai_response=ai_response,
                sources=sources if sources is not None else []
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            # Log the error but don't re-raise, as it's fire-and-forget
            print(f"Error saving chat log: {e}")
            if db:
                db.rollback() # Rollback in case of error
        finally:
            if db:
                db.close()

# Singleton Instance
orchestrator = Orchestrator()
