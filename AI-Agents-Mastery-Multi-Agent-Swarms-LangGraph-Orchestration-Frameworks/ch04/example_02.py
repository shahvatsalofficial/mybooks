# Task 1: Deep Distributed Systems Research
research_task = Task(
    description=(
        "Conduct an in-depth architectural analysis of Distributed Checkpointing in multi-agent systems. "
        "Focus on: 1) Redis vs PostgreSQL state persistence tradeoffs, 2) Concurrency locking mechanisms, "
        "and 3) Recovery time objective (RTO) metrics during network partitions."
    ),
    expected_output=(
        "A structured 3-part technical brief containing comparative latency benchmarks, "
        "failure recovery matrices, and architectural recommendations."
    ),
    agent=cloud_researcher
)

# Task 2: Synthesize Executive Engineering Advisory
publication_task = Task(
    description=(
        "Review the distributed checkpointing research provided by the Principal Architect. "
        "Draft an executive engineering advisory formatted in Markdown with: "
        "- Executive Summary (3 sentences)\n"
        "- Architectural Tradeoff Table\n"
        "- 3 Mandatory Production Implementation Rules"
    ),
    expected_output="A polished, publication-ready Markdown advisory with zero placeholder text.",
    agent=tech_writer
)
