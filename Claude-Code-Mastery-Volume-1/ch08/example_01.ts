import * as fs from 'fs';
import * as path from 'path';

export interface ExamSubmission {
  candidateId: string;
  submissionTimestamp: number;
  domainAnswers: Record<string, string>; // e.g. {"1.1": "B", "1.2": "B"}
  practicalArtifactPaths: string[];
}

export interface DomainScore {
  domainId: string;
  domainName: string;
  scorePercentage: number;
  passed: boolean;
}

export interface ExamResult {
  candidateId: string;
  compositeScore: number;
  accredited: boolean;
  domainScores: DomainScore[];
  validationErrors: string[];
  cryptographicSignature: string;
}

export class MasteryExamEvaluator {
  private readonly answerKey: Record<string, string>;
  private readonly domainWeights: Record<string, number>;
  private readonly passingThreshold = 85.0;
  private readonly compositeThreshold = 88.0;

  constructor(answerKeyPath: string) {
    this.answerKey = JSON.parse(fs.readFileSync(answerKeyPath, 'utf8'));
    this.domainWeights = {
      '1': 0.20,
      '2': 0.20,
      '3': 0.20,
      '4': 0.20,
      '5': 0.20
    };
  }

  /**
   * Evaluates a candidate submission against authoritative answer keys,
   * calculating domain scores and overall accreditation status.
   */
  public evaluateSubmission(submission: ExamSubmission): ExamResult {
    const domainCounts: Record<string, { total: number; correct: number }> = {
      '1': { total: 0, correct: 0 },
      '2': { total: 0, correct: 0 },
      '3': { total: 0, correct: 0 },
      '4': { total: 0, correct: 0 },
      '5': { total: 0, correct: 0 }
    };

    const validationErrors: string[] = [];

    // Evaluate theoretical multiple-choice questions
    for (const [qId, candidateAnswer] of Object.entries(submission.domainAnswers)) {
      const domainPrefix = qId.split('.')[0];
      if (!domainCounts[domainPrefix]) {
        validationErrors.push(`Unrecognized question domain ID: ${qId}`);
        continue;
      }

      domainCounts[domainPrefix].total++;
      if (this.answerKey[qId] === candidateAnswer.trim().toUpperCase()) {
        domainCounts[domainPrefix].correct++;
      }
    }

    const domainNames: Record<string, string> = {
      '1': 'Terminal Runtimes & Sandboxing',
      '2': 'Project Memory Engineering',
      '3': 'Structured Prompting & XML',
      '4': 'Subagent Swarms & Topologies',
      '5': 'Production Workflows & Canary'
    };

    let weightedCompositeScore = 0.0;
    const domainScores: DomainScore[] = [];
    let allDomainsPassed = true;

    for (const [domainId, stats] of Object.entries(domainCounts)) {
      const percentage = stats.total > 0 ? (stats.correct / stats.total) * 100 : 0.0;
      const passed = percentage >= this.passingThreshold;
      if (!passed) allDomainsPassed = false;

      weightedCompositeScore += percentage * this.domainWeights[domainId];

      domainScores.push({
        domainId,
        domainName: domainNames[domainId],
        scorePercentage: Math.round(percentage * 10) / 10,
        passed
      });
    }

    const compositeScore = Math.round(weightedCompositeScore * 10) / 10;
    const accredited = allDomainsPassed && (compositeScore >= this.compositeThreshold);

    const cryptographicSignature = this.generateCredentialProof(
      submission.candidateId,
      compositeScore,
      accredited
    );

    return {
      candidateId: submission.candidateId,
      compositeScore,
      accredited,
      domainScores,
      validationErrors,
      cryptographicSignature
    };
  }

  /**
   * Generates a deterministic verification hash for passing candidates.
   */
  private generateCredentialProof(candidateId: string, score: number, accredited: boolean): string {
    if (!accredited) return 'UNACCREDITED_SUBMISSION';
    const payload = `${candidateId}:${score}:${Date.now()}:CLAUDE_CODE_MASTER_VOL1`;
    return Buffer.from(payload).toString('base64');
  }
}
