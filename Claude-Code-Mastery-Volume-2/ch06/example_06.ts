import { z } from "zod";

export interface EvaluationCritique {
  evaluatorId: string;
  verdict: "APPROVE" | "REJECT" | "REQUEST_CHANGES";
  scoreOutOf10: number;
  criticalRisks: string[];
  rationale: string;
}

export interface CommitteeConsensus {
  approved: boolean;
  quorumType: "UNANIMOUS" | "MAJORITY" | "FAILED";
  averageScore: number;
  aggregatedRisks: string[];
  dissentingOpinions: string[];
}

export class MultiAgentConsensusCommittee {
  /**
   * Coordinates evaluation across three distinct auditor roles.
   */
  public async evaluatePullRequest(
    diffText: string,
    evaluators: Array<(diff: string) => Promise<EvaluationCritique>>
  ): Promise<CommitteeConsensus> {
    console.log(`[CONSENSUS] Dispatching PR diff (${diffText.length} bytes) to ${evaluators.length} independent evaluators...`);

    // Execute evaluations in parallel to minimize latency
    const critiques = await Promise.all(evaluators.map(evaluator => evaluator(diffText)));

    const approvals = critiques.filter(c => c.verdict === "APPROVE").length;
    const rejections = critiques.filter(c => c.verdict === "REJECT").length;
    const avgScore = critiques.reduce((acc, c) => acc + c.scoreOutOf10, 0) / critiques.length;

    const allRisks = critiques.flatMap(c => c.criticalRisks);
    const dissents = critiques.filter(c => c.verdict !== "APPROVE").map(c => `[${c.evaluatorId}]: ${c.rationale}`);

    let quorumType: "UNANIMOUS" | "MAJORITY" | "FAILED" = "FAILED";
    let approved = false;

    if (approvals === critiques.length && avgScore >= 8.0) {
      quorumType = "UNANIMOUS";
      approved = true;
    } else if (approvals >= Math.ceil(critiques.length / 2) && rejections === 0 && avgScore >= 7.0) {
      quorumType = "MAJORITY";
      approved = true;
    }

    return {
      approved,
      quorumType,
      averageScore: Number(avgScore.toFixed(2)),
      aggregatedRisks: Array.from(new Set(allRisks)),
      dissentingOpinions: dissents
    };
  }
}
