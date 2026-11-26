class OrderQueryFilter(BaseModel):
       model_config = ConfigDict(extra="forbid")
       customer_id: int = Field(description="Validated integer customer ID")
       status: Optional[str] = Field(description="Order status enum: PENDING, SHIPPED")
       limit: int = Field(default=10, le=50)
   ```
   The backend handler constructs the query using parameterized SQLAlchemy or PostgreSQL statements: `SELECT * FROM orders WHERE customer_id = $1`.
2. **Read-Only Database Roles**: Tools designed for querying data must connect via strictly read-only database credentials with `DROP`, `ALTER`, and `DELETE` privileges permanently revoked at the PostgreSQL engine level.

### 7.2 Incident Post-Mortem B: The Infinite Tool Call Hallucination Loop

<div class="postmortem-card">
  <span class="postmortem-badge">OPERATIONAL POST-MORTEM</span>
  <h3 style="margin-top:0.4rem; color:#991B1B;">The Infinite Tool Call Deserialization Loop</h3>
  <p><strong>Impact:</strong> 1,200 microservice worker threads locked in an infinite recursive tool dispatch cycle; $18,400 USD burned in 90 minutes; gateway exhaustion.</p>
</div>

#### Incident Narrative & Root Cause Analysis
An enterprise insurance claims system implemented an agentic verification loop. When an incoming medical claim was ingested, the model called a verification tool `validate_claim_icd10(code: str)`.

Due to a schema versioning discrepancy between the frontend client and the backend microservice:
1. The tool handler expected an integer claim ID, but the LLM emitted a string format.
2. The client threw a deserialization error and caught it inside an unconstrained `while True:` loop:
   ```python
   # THE INFINITE LOOP ANTI-PATTERN
   while not success:
       response = client.chat.completions.create(messages=messages, tools=tools)
       # If tool execution fails, append error and repeat without max-turn limit!
   ```
3. Because the error feedback prompt was ambiguous, the model repeatedly emitted the same invalid tool call signature.
4. Each iteration appended more error context to the conversation history, swelling the context from 2,000 tokens to 98,000 tokens.
5. Over 1,200 concurrent claims entered this loop simultaneously, consuming tens of millions of tokens per minute until credit exhaustion halted the account.

#### Remediation
* **Strict Recursion Limits**: Every agentic tool-execution loop must enforce a non-negotiable **Maximum Turn Ceiling** (`MAX_TURNS = 5`).
* **Schema Strictness**: Adopting OpenAI Strict Mode (`strict: true`) permanently eliminates argument deserialization errors, as the gateway masks out type-incompatible tokens before emission.

---

## 8. Comparative Decision Matrix: JSON Extraction Strategies

| Evaluation Dimension | Heuristic Regex Scraping | Legacy JSON Mode (`type: "json_object"`) | Strict Structured Outputs (`response_format`) | Instructor Framework (Pydantic Core) |
| :--- | :--- | :--- | :--- | :--- |
| **Schema Guarantee** | Zero (Frequent syntax & key drift) | Probabilistic (Syntax valid, schema unverified) | **100% Deterministic (Zero Schema Drift)** | **100% Deterministic + Custom Business Logic** |
| **Grammar Enforcement** | None (Post-hoc regex extraction) | Tokenizer heuristic | **Context-Free Grammar Logit Mask** | CFG Mask + Auto-Correction Feedback Loop |
| **Failure Rate (p99)** | 12.4% Syntax Failure | 3.8% Schema Property Missing | **0.00% Schema Failure** | **0.00% Schema Failure** |
| **Latency Penalty** | 0ms overhead | 0ms overhead | 100ms–300ms initial schema compile | 100ms initial compile + retry loop on custom validation failure |
| **Complex Validation (e.g. Sum=1.0)** | Unsupported | Unsupported | Unsupported (CFG cannot count across dynamic floats) | **Supported natively via @field_validator** |
| **Streaming Support** | Unbuffered text parse | Unbuffered text parse | Native token stream | **Native partial object streaming** |
| **Optimal Enterprise Use Case** | Deprecated / Rapid scripts | Unstructured JSON dumping | Production APIs, B2B data integration, ETL | Autonomous agents, complex financial calculations |

---

## 9. Enterprise Production Readiness Checklist & Practice Advisory

> [!IMPORTANT]
> **Production Architectural Rule #1**: *Always enforce `strict: true` on both Function Calling tools and Structured Outputs.* Running function calling in legacy non-strict mode exposes downstream microservices to hallucinated property names, missing required fields, and silent type-coercion bugs.

> [!TIP]
> **Performance Optimization**: For large schemas that undergo frequent deployment cycles, maintain a warm-up invocation in your CI/CD health check. Issuing a single synthetic request with the schema pre-warms OpenAI’s global grammar cache, eliminating the 300ms compilation overhead for your live production users.

### 9.1 Enterprise Structured Output Verification Checklist
* [ ] All Pydantic models inherit `ConfigDict(extra="forbid")` to enforce `additionalProperties: false`.
* [ ] All optional fields are explicitly defined as nullable unions (`Optional[T] = Field(default=None)`).
* [ ] Database query tools use strongly typed, parameterized filters; raw SQL strings from the LLM are strictly banned.
* [ ] Agentic tool loops enforce a hard maximum iteration ceiling (`MAX_TOOL_TURNS <= 5`) to prevent infinite execution loops.
* [ ] Partial tool failures in parallel batches are captured and gracefully re-injected as structured JSON error responses.
* [ ] Tool descriptions are rich, disambiguated, and include operational constraints to maximize routing accuracy.
* [ ] Two-Phase Commit (`prepare` and `commit`) tools are enforced on all mutating database operations.
* [ ] Finite State Machine guards reject out-of-order tool calls before execution.

### 9.2 WebAssembly (Wasm) Micro-Sandboxing for Dynamic Tool Handlers
When an autonomous agent is authorized to execute computational scripts—such as Python code execution, mathematical evaluations, or regex transformations—running that code inside the main host process or a shared container introduces critical security vulnerabilities. If an indirect prompt injection attack breaches the model, malicious Python code can read host environment variables (`OPENAI_API_KEY`, database passwords) or establish outbound socket reverse-shells.

To achieve true zero-trust execution, enterprise architectures deploy **WebAssembly (Wasm) Micro-Sandboxes** (utilizing `wasmtime` or `wasmer` runtimes):

<div class="diagram-container">
  <img src="../assets/svg/diag_ch02_sec_03_wasm_sandbox.svg" alt="Figure 2.7: WebAssembly Sandbox Isolation Boundary" />
  <p class="diagram-caption">Figure 2.7: WebAssembly Sandbox Isolation Boundary</p>
</div>
