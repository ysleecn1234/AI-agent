from typing import List, Dict, Optional
from services.ai_hub.db.hub_repo import HubRepository

class HubManager:
    """
    Core Logic for Agent Hub & Recommendation.
    Delegates DB operations to HubRepository.
    """
    
    def __init__(self):
        self.repo = HubRepository()

    # --- Open Hub Filter Logic ---

    def get_agents(self, db_session, user_profile: Dict, filter_scope: str = "ALL") -> List[object]:
        """
        Fetch agents based on visibility scope.
        Logic:
           - Default ("ALL"): Show ALL public agents (Open Hub).
           - Filter: If user selects specific scope (COMPANY/DEPT/TEAM), apply filter.
        """
        if filter_scope == "ALL":
             return self.repo.get_all_public_agents(db_session)
             
        elif filter_scope == "COMPANY":
             # Implementation dependent on schema
             return self.repo.get_all_public_agents(db_session) # Placeholder
             
        # ... Add detailed filtering logic invoking repo ...
        return self.repo.get_all_public_agents(db_session)

    # --- Search Logic ---

    async def recommend_agents(self, db_session, intent_query: str, top_k: int = 5) -> List[object]:
        """
        Current Implementation: Keyword Search (Name OR Description).
        Future: Hybrid with Vector Search.
        """
        return self.repo.get_agents_by_keyword(db_session, intent_query)
