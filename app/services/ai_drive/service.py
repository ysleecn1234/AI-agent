"""
AI Drive Service Stub
---------------------
This module is the interface for Song Ho-sung's Document Embedding Module.
"""

from typing import List, Dict

class AIDriveService:
    def __init__(self):
        pass

    def get_user_storage_usage(self, user_id: str) -> Dict:
        """
        Stub: Get storage usage stats.
        """
        return {"used_mb": 120, "limit_mb": 1000, "file_count": 15}

    def fetch_available_knowledge(self, user_id: str) -> List[Dict]:
        """
        Stub: List documents available for RAG.
        Used by Agent Wizard Step 2.
        """
        return [
            {"id": "doc-1", "title": "HR Guidelines 2024.pdf", "type": "PDF"},
            {"id": "doc-2", "title": "Q1 Revenue Report.xlsx", "type": "EXCEL"},
            {"id": "doc-3", "title": "Project Alpha Wiki", "type": "NOTION"}
        ]

    def upload_document(self, user_id: str, title: str, content: str):
        """
        Stub: Called by 'Save to Drive' action.
        """
        print(f"[Drive Stub] Uploading document '{title}' for user {user_id}...")
        return {"status": "success", "doc_id": "new-doc-99"}

drive_service = AIDriveService()
