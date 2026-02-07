import uuid
import json
from typing import Optional, Dict

def generate_agent_id() -> str:
    """고유한 에이전트 ID (Draft ID)를 생성합니다."""
    return str(uuid.uuid4())

def safe_json_loads(data: str) -> Optional[Dict]:
    """JSON 문자열을 안전하게 파싱합니다. 실패시 None을 반환하거나 예외처리."""
    try:
        return json.loads(data)
    except:
        return None
