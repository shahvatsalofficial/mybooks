import traceback
from typing import Dict, Any, List, Callable, Optional
from pydantic import BaseModel

class CompensationAction(BaseModel):
    step_name: str
    rollback_handler_name: str
    metadata: Dict[str, Any]

class TransactionalSagaState(TypedDict):
    transaction_id: str
    active_step: str
    allocated_resources: List[str]
    compensation_log: List[Dict[str, Any]]
    execution_error: Optional[str]

class SagaRollbackCoordinator:
    """Executes registered compensation hooks in reverse chronological order."""
    
    def __init__(self):
        self.handlers: Dict[str, Callable[[Dict[str, Any]], bool]] = {}

    def register_handler(self, name: str, fn: Callable[[Dict[str, Any]], bool]):
        self.handlers[name] = fn

    def execute_compensation_saga(self, compensation_log: List[Dict[str, Any]]) -> bool:
        print(f"[SAGA COORDINATOR] Initiating transactional rollback across {len(compensation_log)} registered steps...")
        all_succeeded = True
        
        # Traverse in reverse chronological order (LIFO)
        for record in reversed(compensation_log):
            step = record["step_name"]
            handler_name = record["rollback_handler_name"]
            meta = record["metadata"]
            
            handler = self.handlers.get(handler_name)
            if handler:
                try:
                    success = handler(meta)
                    print(f"  -> [ROLLBACK SUCCESS] {step} via {handler_name}: {meta}")
                except Exception as exc:
                    print(f"  -> [ROLLBACK ERROR] Failed to compensate {step}: {exc}")
                    all_succeeded = False
            else:
                print(f"  -> [CRITICAL] No registered rollback handler for '{handler_name}'!")
                all_succeeded = False
        return all_succeeded

def step_provision_vpc(state: TransactionalSagaState) -> Dict[str, Any]:
    vpc_id = "vpc-091a2bc881"
    print(f"[STEP 1] Provisioned AWS VPC {vpc_id}.")
    record = {
        "step_name": "provision_vpc",
        "rollback_handler_name": "delete_aws_vpc",
        "metadata": {"vpc_id": vpc_id}
    }
    return {
        "allocated_resources": state["allocated_resources"] + [vpc_id],
        "compensation_log": state["compensation_log"] + [record]
    }

def step_failing_database(state: TransactionalSagaState) -> Dict[str, Any]:
    print("[STEP 2] Attempting RDS database provisioning...")
    raise ConnectionRefusedError("Database subnet group failed validation! Simulating node crash.")
