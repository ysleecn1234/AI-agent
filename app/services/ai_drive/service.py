"""
AI Drive Service Integration
----------------------------
Connects the App Shell (FastAPI) to the AI Drive Logic (Feature-H).
"""

import os
import shutil
import tempfile
from typing import List, Dict, Any
from fastapi import UploadFile

# Import Team Code (Feature-H)
from services.ai_drive.pipeline import DocumentPipeline
from services.ai_drive.db.postgres_client import PostgresClient

class AIDriveService:
    def __init__(self):
        # Initialize Team Modules
        self.pipeline = DocumentPipeline()
        self.db_client = PostgresClient()

    def get_user_storage_usage(self, user_id: str) -> Dict:
        """
        Get storage usage stats.
        TODO: Implement real aggregation in PostgresClient.
        For now, returns a dummy value or we could calc it if supported.
        """
        # Feature-H doesn't have a direct 'get_usage' method yet.
        return {"used_mb": 150, "limit_mb": 1000, "file_count": 24}

    def fetch_available_knowledge(self, user_id: str) -> List[Dict]:
        """
        List documents available for RAG.
        Used by Agent Wizard Step 2.
        """
        # Call Feature-H DB Client
        docs = self.db_client.list_documents(
            status="active",
            visibility="team" # Default to team visibility for now
        )
        
        # Format for Frontend
        return [
            {
                "id": doc["doc_id"],
                "title": doc["title"],
                "type": (doc.get("file_type") or "DOC").upper(),
                "created_at": doc.get("created_at")
            }
            for doc in docs
        ]

    def upload_document(self, user_id: str, file: UploadFile, department: str = "General"):
        """
        Handle file upload via Pipeline.
        """
        try:
            # 1. Save to Temp File (Pipeline requires file path)
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = tmp.name

            # 2. Call Feature-H Pipeline
            result = self.pipeline.process_file_upload(
                file_path=tmp_path,
                creator_id=user_id,
                creator_department=department,
                title=file.filename,
                visibility="team"
            )
            
            # 3. Cleanup
            os.remove(tmp_path)
            
            return result

        except Exception as e:
            print(f"[Drive Service] Upload Error: {e}")
            raise e

drive_service = AIDriveService()
