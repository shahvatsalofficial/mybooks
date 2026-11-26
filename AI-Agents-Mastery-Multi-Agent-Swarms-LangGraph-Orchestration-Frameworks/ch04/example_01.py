import os
from typing import List
from crewai import Agent, Task, Crew, Process
from pydantic import BaseModel, Field

# Ensure API Key environment configuration
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "mock-key-for-local-verification")

# 1. Define Senior Technical Researcher Agent
cloud_researcher = Agent(
    role="Principal Distributed Systems Architect",
    goal="Identify and quantify failure recovery patterns in cloud-native microservices.",
    backstory=(
        "You have designed Tier-0 distributed systems handling 500,000 requests per second. "
        "You evaluate architectural tradeoffs through the lens of CAP theorem, tail latency, "
        "and cascading failure prevention."
    ),
    verbose=True,
    memory=True, # Enables short-term session memory
    allow_delegation=False # Leaf worker cannot delegate tasks
)

# 2. Define Staff Technical Writer Agent
tech_writer = Agent(
    role="Staff Technical Publication Strategist",
    goal="Synthesize complex distributed systems research into actionable, publication-grade engineering advisories.",
    backstory=(
        "You are an acclaimed technical author who specializes in translating dense distributed systems "
        "principles into clear, high-signal architectural blueprints for C-suite leaders and Principal Engineers."
    ),
    verbose=True,
    memory=True,
    allow_delegation=False
)
