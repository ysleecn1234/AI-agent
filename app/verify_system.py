import requests
import json
import time

BASE_URL = "http://localhost:8000"

def run_verification():
    print("=== IN7 AI Platform Verification Script ===")
    
    # 1. Health Check
    try:
        res = requests.get(f"{BASE_URL}/health")
        print(f"1. Health Check: {res.status_code} - {res.json()}")
    except Exception as e:
        print(f"Server not running? {e}")
        return

    # 2. Register
    user_email = f"test_{int(time.time())}@in7.co.kr"
    payload = {
        "email": user_email,
        "password": "password123",
        "name": "Tester",
        "department": "QA"
    }
    res = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print(f"2. Register: {res.status_code}")
    if res.status_code != 200:
        print(res.text)
        return
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Chat (Auto Mode)
    chat_payload = {"message": "Hello AI", "model_type": "AUTO"}
    res = requests.post(f"{BASE_URL}/chat/", json=chat_payload, headers=headers)
    print(f"3. Chat: {res.status_code} - {res.json().get('response')}")

    # 4. Agent Wizard: Create Draft
    draft_payload = {"selected_messages": [{"role": "user", "content": "Hello AI"}]}
    res = requests.post(f"{BASE_URL}/agents/draft", json=draft_payload, headers=headers)
    print(f"4. Create Draft: {res.status_code}")
    draft_id = res.json().get("draft_id")

    # 5. Agent Wizard: List Drafts
    res = requests.get(f"{BASE_URL}/agents/drafts", headers=headers)
    print(f"5. List Drafts: {res.status_code} - Count: {len(res.json())}")

    # 6. Agent Wizard: Publish
    # Skip Step 1/2 for speed, just try publish (might fail if fields missing? No, draft has defaults)
    pub_payload = {"draft_id": draft_id}
    res = requests.post(f"{BASE_URL}/agents/publish", json=pub_payload, headers=headers)
    print(f"6. Publish Agent: {res.status_code}")
    if res.status_code == 200:
        print(f"   Agent ID: {res.json().get('agent_id')}")

    # 7. Hub List
    res = requests.get(f"{BASE_URL}/integrations/hub/list", headers=headers)
    print(f"7. Hub List: {res.status_code} - Count: {len(res.json())}")

if __name__ == "__main__":
    run_verification()
