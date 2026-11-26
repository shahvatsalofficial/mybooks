SET lock_timeout = '2s';
   ALTER TABLE orders DROP COLUMN billing_address_id;
   ```

If the lock could not be acquired within two seconds, the statement aborted cleanly, preventing request queuing and preserving 100% production uptime.

---

## 4. Case Study 3: Autonomous Test Suite Synthesis (0% to 92% Coverage)

### The Production Scenario
A Tier-1 financial payments gateway acquired an enterprise identity verification platform. The acquisition audit revealed a critical engineering liability: the core biometric fraud-detection microservice—comprising 52,000 lines of complex, high-concurrency Python and C++ bindings—had **0.0% automated unit or integration test coverage**.

The service had been maintained for five years by a small group of founding engineers who relied entirely on manual end-to-end testing against staging hardware. The code was rife with deeply nested conditional branches (cyclomatic complexity reaching $M = 48$ in critical validation functions), implicit dependencies on local file-system temp directories, and unmocked calls to third-party government identification registries.

The security engineering steering committee mandated an immediate freeze on all feature development until the repository achieved **at least 85% branch coverage** and passed strict mutation testing audits. Estimated human engineering time to manually write this test base: **6 developer-months**.

<div class="diagram-container">
  <img src="assets/svg/diag_ch07_case3_test_gen.svg" alt="Figure 7.3: Autonomous Test Suite Synthesis: Branch Coverage &amp; Boundary Fuzzing Engine" style="width: 100%; height: auto; display: block;" />
</div>

### Architectural Workflow: Property-Based Synthesis & Mutation Fuzzing

Writing naive tests using basic LLM prompts typically yields shallow, brittle assertions that test trivial happy paths while ignoring boundary failures. To construct an enterprise-grade test base, the engineering team engineered an autonomous synthesis harness using Claude Code, combining **Property-Based Testing (Hypothesis)** with **Mutation Score Verification (Mutmut)**.

#### Step 1: Control Flow Graph & AST Branch Dissection
Claude was invoked via a batch script to analyze the AST of every module in `src/fraud/`. Using Python’s `ast` module, the agent extracted every:
- Conditional statement (`If`, `Elif`, `Else`).
- Exception handling block (`Try`, `Except`, `Finally`).
- Comparison operator (`Eq`, `NotEq`, `Lt`, `GtE`, `In`, `Is`).
- Return path and yield expression.

For each function, the agent computed McCabe’s Cyclomatic Complexity metric ($M = E - N + 2P$, where $E$ is the number of edges, $N$ is the number of nodes, and $P$ is the number of connected components). Functions with $M > 25$ were flagged for multi-phase decomposition. For each target, the agent generated a structured **Branch Matrix**: a comprehensive table enumerating all theoretical combinatorial execution paths required to achieve full mathematical branch coverage.

#### Step 2: Hermetic Sandbox & External Dependency Mocking
Before writing assertions, the agent isolated the environment. It constructed a centralized `conftest.py` harness featuring pytest fixtures that intercepted and hermetically stubbed all external interactions:
- Network sockets (via `pytest-responses` and `pytest-mock`).
- Database engines (spawning temporary SQLite in-memory databases with identical schemas).
- File system reads/writes (utilizing Python’s `tmp_path` fixture).
- System clocks (using `freezegun` to freeze time and eliminate non-deterministic timestamp assertions).

#### Step 3: Property-Based Invariant Fuzzing
Rather than writing hardcoded test assertions with static values (e.g., verifying hardcoded user names and static IDs), Claude was instructed to write **Property-Based Invariant Tests** using the `hypothesis` library.

The agent formulated universal mathematical and business invariants for the fraud detection algorithms:
1. **Idempotence**: Evaluating the same user profile twice must yield identical risk scores.
2. **Monotonicity**: Increasing verified identity attributes must never increase the fraud risk coefficient.
3. **Boundary Resilience**: The engine must never crash or throw unhandled exceptions regardless of input string encoding, null bytes, negative timestamps, or astronomical integer values.
