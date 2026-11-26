from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

api_app = FastAPI(title="LangGraph Enterprise Execution Engine")

class AgentExecutionRequest(BaseModel):
    thread_id: str
    topic: str

class AgentExecutionResponse(BaseModel):
    thread_id: str
    is_approved: bool
    revisions: int
    final_output: Optional[str]

@api_app.post("/api/v1/agent/run", response_model=AgentExecutionResponse)
async def run_agent_endpoint(req: AgentExecutionRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    input_payload: ResearchGraphState = {
        "topic": req.topic,
        "draft_content": "",
        "audit_notes": [],
        "revision_count": 0,
        "is_approved": False,
        "final_output": None
    }
    
    try:
        result = app.invoke(input_payload, config)
        return AgentExecutionResponse(
            thread_id=req.thread_id,
            is_approved=result["is_approved"],
            revisions=result["revision_count"],
            final_output=result.get("final_output")
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Graph execution failed: {str(exc)}")
