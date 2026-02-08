
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from application.usecases.ai_agent.service import AgentService

@pytest.mark.asyncio
async def test_recommendation_ui_data():
    """
    UI 표시에 필요한 데이터(적합도, 작성자, 사용횟수)가 포함되어 있는지 확인
    """
    
    # Setup Mocks
    mock_pipeline = AsyncMock()
    # Mock Translation Analysis
    mock_pipeline.recommend_agents.return_value = {
        "topic": "Python Coding",
        "category": "CODING"
    }
    
    # We don't need to mock agent_manager search logic because we modified the actual class method
    # BUT since we are patching the import in service, we need to ensure we use the real or updated logic.
    # Actually service imports singleton 'agent_manager'.
    # For this test, let's just let it run with the real AgentManager's mock method we just updated.
    # So we only patch Orchestrator pipeline.
    
    with patch("application.usecases.orchestrator.service.orchestrator.pipeline", mock_pipeline):
        service = AgentService()
        
        print("\n[Test] Requesting Recommendation for 'Python coding'...")
        agents = await service.recommend_agents_for_chat("Help me code")
        
        # Verify
        assert len(agents) > 0
        agent = agents[0]
        
        print(f"\n[Result] Agent Found: {agent['name']}")
        print(f" - Match Score: {agent.get('match_score')}%")
        print(f" - Author: {agent.get('author')}")
        print(f" - Usage: {agent.get('usage_count')} times")
        
        # UI Requirement Check
        assert "match_score" in agent
        assert "author" in agent
        assert "usage_count" in agent
        assert "id" in agent # Essential for Actions
        
        print("\n[Success] Data structure is ready for UI Cards! ✨")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_recommendation_ui_data())
