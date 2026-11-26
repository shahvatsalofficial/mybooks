stage_3_prompt = STAGE_3_TEMPLATE.format(
       customer_tier=stage_1_output.tier,
       claim_amount=stage_2_output.approved_amount
   )
   ```
3. **Zero Token Bleed**: Downstream generation stages operate within pristine context windows (< 1,200 tokens), maximizing attention fidelity on their specific deliverable while conserving precious KV-cache capacity across the fleet.

---

## 3. Mathematical Foundations of Pipeline Error Decay

### 3.1 Compound Reliability in Multi-Stage Topologies

Let a pipeline consist of $K$ sequential stages $f_1, f_2, \dots, f_K$. Let $p_i$ denote the probability that stage $i$ executes successfully without semantic deviation or schema failure, conditioned on receiving valid input from stage $i-1$:

$$p_i = P(f_i(y_{i-1}) = y_i^* \mid y_{i-1} = y_{i-1}^*)$$

Under an un-guarded pipeline with no feedback loops or verification firewalls, the end-to-end success probability of the entire chain decays exponentially:

$$P(\text{Pipeline Success}) = \prod_{i=1}^K p_i$$

For a 5-stage pipeline where each individual stage boasts an impressive 95% individual success rate ($p_i = 0.95$):

$$P(\text{Pipeline Success}) = (0.95)^5 \approx 0.7738 = 77.4\%$$

Nearly **one in four requests fails** despite high individual stage performance.

### 3.2 The Mathematical Impact of Inline Re-try Firewalls

When an evaluation firewall with automated retry loops is interposed after each stage, the reliability dynamics change completely. Let $r$ be the maximum allowed retry attempts per stage, and let $q_i$ be the detection recall of the firewall (the probability that an error is correctly caught and triggered for retry).

The effective success probability of stage $i$ becomes:

$$p_i^{\text{guarded}} = 1 - (1 - p_i) \cdot (1 - q_i)^r$$

Assuming $p_i = 0.95$, firewall detection recall $q_i = 0.90$, and a single retry attempt ($r = 1$):

$$p_i^{\text{guarded}} = 1 - (1 - 0.95) \cdot (1 - 0.90) = 1 - (0.05 \cdot 0.10) = 1 - 0.005 = 0.995 = 99.5\%$$

The end-to-end success rate of the entire 5-stage pipeline across all stages elevates from **77.4% to 97.5%**:

$$P(\text{Pipeline Success}_{\text{guarded}}) = (0.995)^5 \approx 97.5\%$$

This mathematical transformation demonstrates why evaluation firewalls are non-negotiable in production prompt chaining architectures.

### 3.3 Dynamic Model Tiering and FinOps Cost Optimization

A transformative advantage of prompt chaining is **Heterogeneous Model Tiering**. In a monolithic prompt, the developer must select the largest, most expensive model (e.g., Claude 3.5 Sonnet or GPT-4o) to satisfy the hardest constraint of the prompt, paying top-tier pricing for trivial sub-tasks.

In a chained pipeline, tasks are mapped to optimal model tiers based on computational complexity:

$$\text{Cost}_{\text{Chained}} = \sum_{i=1}^K N_{\text{tokens}}^{(i)} \cdot \text{Rate}(M_i)$$

Where $M_i \in \{\text{Lightweight Tier}, \text{Mid Tier}, \text{Frontier Tier}\}$.

Consider a high-volume pipeline processing insurance claims:
1. **Stage 1: Document Classification**: Handled by **Claude 3.5 Haiku** ($0.80 / M tokens) $\to$ 99.8% accuracy.
2. **Stage 2: Entity & Table Extraction**: Handled by **Claude 3.5 Haiku** with schema enforcement $\to$ 99.1% accuracy.
3. **Stage 3: Complex Fraud & Policy Reasoning**: Routed to **Claude 3.5 Sonnet** ($3.00 / M tokens) $\to$ High cognitive reasoning.
4. **Stage 4: Customer Summary Generation**: Handled by **Claude 3.5 Haiku** $\to$ High-speed formatting.

By restricting the expensive frontier model to the 20% of the workflow that genuinely requires deep reasoning, the enterprise reduces overall pipeline token costs by **68%** while maintaining identical output quality.

### 3.4 Queueing Theory & Little’s Law Applied to Pipeline Concurrency

When orchestrating chained pipelines at scale (e.g., 10,000 requests/minute), downstream model rate limits and API burst capacities become the critical operational bottleneck. We model the end-to-end pipeline using **Jackson Queueing Networks** and **Little’s Law**:

$$L = \lambda \cdot W$$

Where $L$ is the average number of active pipeline requests in flight, $\lambda$ is the arrival rate of customer queries, and $W = \sum_{i=1}^K W_i$ is the average end-to-end pipeline latency across all $K$ sequential stages.

If stage 2 (e.g., a heavy extraction stage) experiences latency degradation from $W_2 = 1.2\text{s}$ to $W_2 = 4.5\text{s}$ due to upstream cloud provider rate-limiting:
- The total system concurrency $L$ triples,
- In-memory buffer queues in the application gateway overflow, and
- Downstream stages experience catastrophic connection starvation.

To preserve end-to-end P99 SLA guarantees, production prompt chain orchestrators implement **Token Bucket Backpressure Governors**: each stage maintains an independent token replenishment bucket. If stage $i$'s remaining quota drops below $20\%$, the orchestrator immediately throttles admission at stage 1, shedding non-critical background traffic and shielding production transactional workflows.

---

## 4. Production Code Recipes

The following recipes demonstrate complete production-grade implementations of Prompt Chaining pipelines using Python 3.11+, Pydantic v2, and Anthropic Claude APIs, featuring sequential DAG execution, conditional routing gates, inline evaluation firewalls, and parallel map-reduce aggregators.

### Recipe 05.01: Production DAG Sequential Pipeline with Pydantic Schema Contracts

This recipe implements a robust sequential pipeline where intermediate outputs are strictly validated against Pydantic schemas before being injected as inputs into downstream stages.
