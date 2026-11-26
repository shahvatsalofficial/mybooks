from fastapi import FastAPI, BackgroundTasks, HTTPException
import uvicorn

crew_api = FastAPI(title="Enterprise CrewAI Execution Service")

@crew_api.post("/api/v1/crews/research/execute")
async def execute_crew_endpoint(topic: str, background_tasks: BackgroundTasks):
    job_id = f"CREW-RUN-{uuid.uuid4().hex[:8].upper()}"
    print(f"[API GATEWAY] Received execution request for topic '{topic}'. Job ID: {job_id}")
    
    # Run in thread pool to prevent blocking async event loop
    def _run_crew():
        inputs = {"topic": topic}
        publishing_crew.kickoff(inputs=inputs)
        print(f"[BACKGROUND WORKER] Completed Job {job_id}.")
        
    background_tasks.add_task(_run_crew)
    return {"status": "QUEUED", "job_id": job_id, "estimated_duration_sec": 35}
