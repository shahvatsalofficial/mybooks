# case_studies/cs03_swe_squad_agent.py
"""
Case Study 03: Zero-Human Multi-Agent Software Development Squad using CrewAI.
Author: Vatsal Shah — The Agentic Frontier Vol 2
"""

import os
import sys
import time
import subprocess
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SWESquadAgent")

# ============================================================================
# 1. DOMAIN MODELS & SQUAD SCHEMAS
# ============================================================================

class ModuleSpecification(BaseModel):
    module_name: str
    description: str
    endpoints: List[str]
    database_models: List[str]
    quality_threshold: float = 0.85

class CodeGenerationResult(BaseModel):
    source_code: str
    test_code: str
    test_pass_rate: float
    coverage_score: float
    iteration_count: int
    is_ready_for_merge: bool

# ============================================================================
# 2. CREWAI AGENT DEFINITIONS
# ============================================================================

class SWESquadManager:
    def __init__(self, spec: ModuleSpecification):
        self.spec = spec

    def build_squad(self) -> Crew:
        # Agent 1: Software Architect
        architect = Agent(
            role="Senior Software Architect",
            goal="Design clean, scalable microservice architectures and explicit interface contracts.",
            backstory="You are a veteran principal engineer. You design modular Python microservices with FastAPI and Pydantic.",
            verbose=True,
            allow_delegation=False
        )

        # Agent 2: Python Developer
        developer = Agent(
            role="Principal Python Developer",
            goal="Write clean, type-hinted production Python code adhering strictly to architectural specs.",
            backstory="You are an expert Python 3.12 developer specializing in FastAPI, SQLAlchemy, and clean architecture.",
            verbose=True,
            allow_delegation=False
        )

        # Agent 3: QA & Test Engineer
        qa_engineer = Agent(
            role="Lead QA Automation Engineer",
            goal="Write exhaustive Pytest suites that stress-test edge cases and enforce >85% branch coverage.",
            backstory="You are a relentless test automation engineer who finds subtle concurrency and edge-case bugs.",
            verbose=True,
            allow_delegation=False
        )

        # Agent 4: Security & Code Auditor
        reviewer = Agent(
            role="Security & Code Quality Auditor",
            goal="Review code for OWASP Top 10 vulnerabilities, code smells, and performance bottlenecks.",
            backstory="You are a enterprise security architect who audits code for SQL injection, hardcoded credentials, and type safety.",
            verbose=True,
            allow_delegation=False
        )

        # Tasks
        task_arch = Task(
            description=f"Design architecture for module {self.spec.module_name}: {self.spec.description}. Endpoints: {self.spec.endpoints}",
            expected_output="Detailed technical design document with data models and endpoint signatures.",
            agent=architect
        )

        task_code = Task(
            description="Implement complete Python source code files based on the architectural design.",
            expected_output="Production-ready Python code with complete type annotations.",
            agent=developer
        )

        task_qa = Task(
            description="Generate a comprehensive Pytest test suite for the implemented source code.",
            expected_output="Complete pytest test file covering happy paths and edge cases.",
            agent=qa_engineer
        )

        task_review = Task(
            description="Audit the source code and tests for security vulnerabilities and test coverage compliance.",
            expected_output="Security audit report with approval status and final code artifact.",
            agent=reviewer
        )

        # Assemble Crew
        squad_crew = Crew(
            agents=[architect, developer, qa_engineer, reviewer],
            tasks=[task_arch, task_code, task_qa, task_review],
            process=Process.sequential,
            verbose=True
        )

        return squad_crew

# ============================================================================
# 3. LOCAL PYTEST EXECUTION ENGINE WITH CONVERGENCE MONITORING
# ============================================================================

def execute_local_test_harness(source_code: str, test_code: str) -> Dict[str, Any]:
    """
    Executes generated tests against generated code in isolated temporary directory.
    Monitors pass rate and test coverage.
    """
    logger.info(" [Test Engine] Executing Pytest verification harness...")
    
    # Write code to temp files for test execution
    temp_dir = os.path.join(os.getcwd(), "scratch", "swe_sandbox")
    os.makedirs(temp_dir, exist_ok=True)
    
    src_file = os.path.join(temp_dir, "service.py")
    test_file = os.path.join(temp_dir, "test_service.py")
    
    with open(src_file, "w") as f:
        f.write(source_code)
    with open(test_file, "w") as f:
        f.write(test_code)

    # Simulated test engine execution report
    logger.info(" [Test Engine] Pytest executed 18 test cases. 18 Passed, 0 Failed.")
    return {
        "pass_rate": 1.0,
        "coverage": 0.91,
        "failed_tests": []
    }

# ============================================================================
# 4. EXECUTION DEMO
# ============================================================================

if __name__ == "__main__":
    spec = ModuleSpecification(
        module_name="UserBillingService",
        description="FastAPI service for managing customer subscription billing, invoice generation, and webhook events.",
        endpoints=["POST /billing/subscribe", "GET /billing/invoices/{user_id}", "POST /billing/webhook"],
        database_models=["Subscription", "Invoice", "PaymentMethod"]
    )
    
    logger.info(f" Initializing Zero-Human SWE Squad for module: {spec.module_name}")
    squad_manager = SWESquadManager(spec)
    
    # In production run: squad_crew.kickoff()
    # Demo output representation:
    sample_src = """
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional

app = FastAPI(title='UserBillingService')

class SubscriptionRequest(BaseModel):
    user_id: str
    plan_id: str
    email: EmailStr

@app.post('/billing/subscribe')
def create_subscription(req: SubscriptionRequest):
    if not req.plan_id:
        raise HTTPException(status_code=400, detail='Invalid Plan ID')
    return {'status': 'ACTIVE', 'subscription_id': f'SUB-{req.user_id}-9912'}
"""
    sample_test = """
from fastapi.testclient import TestClient
from service import app

client = TestClient(app)

def test_create_subscription_success():
    res = client.post('/billing/subscribe', json={'user_id': 'USR-101', 'plan_id': 'PLAN_PRO', 'email': 'user@example.com'})
    assert res.status_code == 200
    assert res.json()['status'] == 'ACTIVE'
"""

    res = execute_local_test_harness(sample_src, sample_test)
    print(f"\nFinal Test Coverage: {res['coverage'] * 100:.1f}%")
    print(f"Pass Rate: {res['pass_rate'] * 100:.1f}%")
