from __future__ import annotations

from pydantic import BaseModel, Field


class RootCauseCandidate(BaseModel):
    hypothesis_id: str
    category: str
    description: str
    prior_prob: float = Field(gt=0.0, lt=1.0)
    metric_likelihood: float = Field(gt=0.0)
    log_likelihood: float = Field(gt=0.0)
    git_likelihood: float = Field(gt=0.0)
    posterior_prob: float = 0.0


def rank_root_causes(candidates: list[RootCauseCandidate]) -> list[RootCauseCandidate]:
    unnormalized: list[tuple[RootCauseCandidate, float]] = []
    for cand in candidates:
        score = cand.prior_prob * cand.metric_likelihood * cand.log_likelihood * cand.git_likelihood
        unnormalized.append((cand, score))

    total = sum(score for _, score in unnormalized) or 1.0
    ranked: list[RootCauseCandidate] = []
    for cand, score in unnormalized:
        updated = cand.model_copy(update={"posterior_prob": round(score / total, 4)})
        ranked.append(updated)

    return sorted(ranked, key=lambda c: c.posterior_prob, reverse=True)


if __name__ == "__main__":
    hypotheses = [
        RootCauseCandidate(
            hypothesis_id="HYP-DEPLOY-DB-POOL",
            category="bad_deployment",
            description="Commit 9f3a2c1 exhausted DB connection pool via unindexed JSONB query",
            prior_prob=0.35,
            metric_likelihood=0.92,
            log_likelihood=0.95,
            git_likelihood=0.88,
        ),
        RootCauseCandidate(
            hypothesis_id="HYP-REDIS-TIMEOUT",
            category="downstream_dependency",
            description="Redis cluster transient network partition",
            prior_prob=0.20,
            metric_likelihood=0.45,
            log_likelihood=0.25,
            git_likelihood=0.10,
        ),
        RootCauseCandidate(
            hypothesis_id="HYP-TRAFFIC-SPIKE",
            category="capacity_exhaustion",
            description="Organic Black Friday RPS surge beyond HPA maxReplicas",
            prior_prob=0.25,
            metric_likelihood=0.60,
            log_likelihood=0.20,
            git_likelihood=0.15,
        ),
    ]
    for ranked in rank_root_causes(hypotheses):
        print(f"{ranked.hypothesis_id}: posterior={ranked.posterior_prob:.4f} ({ranked.description})")
