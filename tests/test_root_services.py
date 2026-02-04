import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

# Mock Environment
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"

async def test_integration():
    print("====== Testing Root Services Integration (Hub Integrated) ======")
    
    # 1. Test App Wrapper -> Root Service Call
    try:
        from app.services.ai_agent.service import agent_service
        print("[Pass] Successfully imported app.services.ai_agent.service")
    except ImportError as e:
        print(f"[Fail] Import Error: {e}")
        return

    # 2. Test Agent Manager Draft Logic (via Wrapper)
    if hasattr(agent_service, "create_draft"):
        print("[Pass] 'create_draft' method exists in wrapper.")
    else:
        print("[Fail] 'create_draft' missing.")

    # 3. Test Direct Import of Hub Core
    try:
        from services.ai_hub.core.hub import HubManager
        hm = HubManager()
        print("[Pass] Successfully imported services.ai_hub.core.hub.HubManager")
    except ImportError as e:
        print(f"[Fail] Hub Manager Import Error: {e}")

    # 4. Test Direct Import of Agent Core
    try:
        from services.ai_hub.core.agent import AgentManager
        am = AgentManager()
        print("[Pass] Successfully imported services.ai_hub.core.agent.AgentManager")
    except ImportError as e:
        print(f"[Fail] Agent Manager Import Error: {e}")

    print("====== Integration Check Complete ======")

if __name__ == "__main__":
    asyncio.run(test_integration())
