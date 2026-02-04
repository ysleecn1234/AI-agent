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

    async def analyze_for_draft(self, messages: List[Dict]) -> Dict:
        """
        Analyzes conversation history to generate an Agent Draft.
        Uses the pipeline to extract key information from the conversation.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Dictionary with agent draft information
        """
        # Combine messages into a single prompt
        conversation_text = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in messages
        ])
        
        # Create a prompt for agent generation
        prompt = f"""다음 대화 내용을 분석하여 에이전트를 생성하기 위한 정보를 추출해주세요:

{conversation_text}

다음 형식으로 답변해주세요:
1. 에이전트 이름: [간단하고 명확한 이름]
2. 설명: [에이전트의 역할과 목적]
3. 시스템 프롬프트: [에이전트가 사용할 지시사항]
4. 입력 예시: [사용자가 입력할 예시]
5. 출력 예시: [에이전트가 생성할 예시]
"""
        
        # Use pipeline to generate analysis
        result = self.pipeline_without_rag.process(user_input=prompt, user_id=None)
        
        # Parse the response (simplified - in production, use structured output)
        response_text = result.get("response", "")
        
        # TODO: Implement proper parsing of the response
        # For now, return a structured format
        return {
            "name": "Generated Agent",
            "description": "Auto-generated from conversation analysis",
            "system_prompt": response_text[:200] if response_text else "You are a helpful assistant...",
            "input_example": "Help me with...",
            "output_example": "Here is the answer..."
        }

# Singleton Instance
orchestrator = Orchestrator()
