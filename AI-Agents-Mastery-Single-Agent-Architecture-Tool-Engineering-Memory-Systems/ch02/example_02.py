from dataclasses import dataclass, field
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class PlanTask:
    task_id: int
    description: str
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None

class PlanAndSolveOrchestrator:
    def __init__(self, planner_fn: Callable[[str], List[str]], executor_fn: Callable[[str], str]):
        self.planner_fn = planner_fn
        self.executor_fn = executor_fn
        self.plan: List[PlanTask] = []

    def initialize_plan(self, high_level_goal: str):
        raw_steps = self.planner_fn(high_level_goal)
        self.plan = [PlanTask(task_id=i+1, description=step) for i, step in enumerate(raw_steps)]

    def execute_plan(self) -> Dict[str, Any]:
        for task in self.plan:
            if task.status != TaskStatus.PENDING:
                continue
            
            task.status = TaskStatus.IN_PROGRESS
            try:
                # Execute individual planned task
                res = self.executor_fn(task.description)
                task.result = res
                task.status = TaskStatus.COMPLETED
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.result = f"Error: {str(e)}"
                # Trigger replanning phase
                self._replan(failed_task=task)
                break
        
        return {
            "all_completed": all(t.status == TaskStatus.COMPLETED for t in self.plan),
            "tasks": [{"id": t.task_id, "desc": t.description, "status": t.status.value, "result": t.result} for t in self.plan]
        }

    def _replan(self, failed_task: PlanTask):
        replan_prompt = f"Task '{failed_task.description}' failed with '{failed_task.result}'. Generate an alternate sequence."
        new_steps = self.planner_fn(replan_prompt)
        max_id = max(t.task_id for t in self.plan)
        for i, step in enumerate(new_steps):
            self.plan.append(PlanTask(task_id=max_id + i + 1, description=step))

# Verification
def mock_planner(goal: str) -> List[str]:
    return [
        "1. Verify database read replica health",
        "2. Execute keyset pagination scan",
        "3. Export metrics to Prometheus"
    ]

def mock_executor(step_desc: str) -> str:
    return f"Success: Executed {step_desc}"

orchestrator = PlanAndSolveOrchestrator(planner_fn=mock_planner, executor_fn=mock_executor)
orchestrator.initialize_plan("Audit and export metrics for Q3 data cluster.")
summary = orchestrator.execute_plan()
print("Plan Execution Summary:")
print(json.dumps(summary, indent=2))
