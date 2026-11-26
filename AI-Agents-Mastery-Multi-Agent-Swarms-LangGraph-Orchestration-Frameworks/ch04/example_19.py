class AsyncCrewTaskDispatcher:
    def __init__(self, crew: Crew):
        self.crew = crew

    def dispatch_background_task(self, task_inputs: Dict[str, Any]) -> str:
        job_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
        print(f"[ASYNC DISPATCH] Spawning background worker for {job_id}...")
        # In production: celery_app.send_task("run_crew", args=[task_inputs])
        return job_id
