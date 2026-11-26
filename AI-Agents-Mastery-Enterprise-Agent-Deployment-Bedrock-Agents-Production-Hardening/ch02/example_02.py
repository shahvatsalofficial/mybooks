import os
import time
import json
from typing import List, Dict, Any, Optional
from google.cloud import firestore
from google.oauth2 import service_account

class FirestoreSessionManager:
    """Enterprise persistent session backend for Google ADK agents using Google Cloud Firestore."""

    def __init__(self, project_id: str, collection_name: str = "adk_agent_sessions"):
        self.db = firestore.Client(project=project_id)
        self.collection = self.db.collection(collection_name)

    def create_or_resume_session(self, session_id: str, user_id: str, ttl_days: int = 30) -> Dict[str, Any]:
        """Initializes or retrieves an agent session record."""
        doc_ref = self.collection.document(session_id)
        doc = doc_ref.get()
        
        now = int(time.time())
        expires_at = now + (ttl_days * 86400)
        
        if doc.exists:
            data = doc.to_dict()
            doc_ref.update({"last_accessed": now, "expires_at": expires_at})
            return data
        else:
            initial_data = {
                "session_id": session_id,
                "user_id": user_id,
                "created_at": now,
                "last_accessed": now,
                "expires_at": expires_at,
                "turn_count": 0,
                "messages": [],
                "memory_context": {}
            }
            doc_ref.set(initial_data)
            return initial_data

    def append_turn(self, session_id: str, role: str, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None) -> None:
        """Appends a turn to the session with atomic transaction."""
        doc_ref = self.collection.document(session_id)
        turn = {
            "role": role,
            "content": content,
            "tool_calls": tool_calls or [],
            "timestamp": int(time.time())
        }
        
        doc_ref.update({
            "messages": firestore.ArrayUnion([turn]),
            "turn_count": firestore.Increment(1),
            "last_accessed": int(time.time())
        })

    def get_history_for_gemini(self, session_id: str, max_turns: int = 20) -> List[Dict[str, Any]]:
        """Extracts history formatted for Gemini SDK multi-turn chats."""
        doc = self.collection.document(session_id).get()
        if not doc.exists:
            return []
        
        data = doc.to_dict()
        messages = data.get("messages", [])[-max_turns:]
        
        gemini_history = []
        for msg in messages:
            gemini_role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({
                "role": gemini_role,
                "parts": [{"text": msg["content"]}]
            })
        return gemini_history

if __name__ == "__main__":
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "demo-gcp-enterprise")
    sm = FirestoreSessionManager(project_id=project)
    
    sess = sm.create_or_resume_session("sess-k8s-triage-4091", "sre-engineer-77")
    print(f"Session {sess['session_id']} initialized for {sess['user_id']}.")
    
    sm.append_turn("sess-k8s-triage-4091", "user", "Pod payment-gateway-6f9d is OOMKilled in prod-east.")
    sm.append_turn("sess-k8s-triage-4091", "model", "Investigating container memory limits and heap telemetry.")
    
    hist = sm.get_history_for_gemini("sess-k8s-triage-4091")
    print("Current Gemini History Length:", len(hist))
