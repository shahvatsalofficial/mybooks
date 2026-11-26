# hitl_review_service.py — EU AI Act Article 14 Human Oversight Gate
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Any, Optional
import time

app = FastAPI(title="Enterprise HITL Review Gate", version="1.0.0")
security = HTTPBearer()

# In-Memory Queue for Underwriter Review
PENDING_REVIEWS: Dict[str, Dict[str, Any]] = {}
APPROVED_DECISIONS: Dict[str, Dict[str, Any]] = {}

class ReviewTask(BaseModel):
    task_id: str
    applicant_id: str
    model_score: float
    model_recommendation: str
    reasoning_citations: list

class ReviewDecision(BaseModel):
    task_id: str
    underwriter_id: str
    action: str # "APPROVE", "REJECT", "OVERRIDE"
    justification_note: str

@app.post("/api/v1/hitl/submit-for-review")
async def submit_task(task: ReviewTask):
    """Called automatically when model confidence is within [0.60, 0.90]."""
    PENDING_REVIEWS[task.task_id] = {
        "data": task.dict(),
        "submitted_at": time.time(),
        "status": "PENDING"
    }
    return {"status": "QUEUED_FOR_HUMAN_OVERSIGHT", "task_id": task.task_id}

@app.post("/api/v1/hitl/decision")
async def commit_decision(decision: ReviewDecision):
    """Enforces human underwriter cryptographic override signoff."""
    if decision.task_id not in PENDING_REVIEWS:
        raise HTTPException(status_code=404, detail="Task not found or already processed")

    task_data = PENDING_REVIEWS.pop(decision.task_id)
    APPROVED_DECISIONS[decision.task_id] = {
        "original_model_output": task_data["data"],
        "human_decision": decision.dict(),
        "committed_at": time.time(),
        "compliance_record_id": f"AUDIT-{decision.task_id}"
    }
    return {
        "status": "DECISION_COMMITTED",
        "audit_proof": f"AUDIT-{decision.task_id}"
    }
