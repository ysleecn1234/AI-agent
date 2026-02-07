from typing import List, Dict, Optional
from services.ai_hub.db.hub_repo import HubRepository

class HubManager:
    """
    Agent Hub 및 추천을 위한 핵심 로직.
    DB 작업은 HubRepository에 위임합니다.
    """
    
    def __init__(self):
        self.repo = HubRepository()

    # --- Open Hub 필터 로직 ---

    def get_agents(self, db_session, user_profile: Dict, filter_scope: str = "ALL") -> List[object]:
        """
        공개 범위(Visibility Scope)에 따라 에이전트를 조회합니다.
        로직:
           - 기본값 ("ALL"): 모든 공개 에이전트 표시 (Open Hub).
           - 필터: 사용자가 특정 범위(전사/부서/팀)를 선택하면 해당 필터 적용.
        """
        if filter_scope == "ALL":
             return self.repo.get_all_public_agents(db_session)
             
        elif filter_scope == "COMPANY":
             # 스키마에 따라 구현 필요
             return self.repo.get_all_public_agents(db_session) # Placeholder
             
        # ... 리포지토리를 호출하는 상세 필터링 로직 추가 ...
        return self.repo.get_all_public_agents(db_session)

    # --- 검색 로직 ---

    async def recommend_agents(self, db_session, intent_query: str, top_k: int = 5) -> List[object]:
        """
        현재 구현: 키워드 검색 (이름 또는 설명).
        향후 계획: 벡터 검색과의 하이브리드 검색.
        """
        return self.repo.get_agents_by_keyword(db_session, intent_query)
