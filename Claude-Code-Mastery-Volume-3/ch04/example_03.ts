import {
  proxyActivities,
  defineSignal,
  defineQuery,
  setHandler,
  condition,
  ApplicationFailure,
} from '@temporalio/workflow';
import type * as activities from './activities';

// Activity Proxy with robust retry policies
const {
  provisionCleanroomVolume,
  acquireDistributedGitLock,
  executeReActReasoningTurn,
  runAutomatedTestVerification,
  createCryptographicAuditBlock,
  dispatchSignedPullRequest,
  releaseDistributedGitLock,
  destroyCleanroomVolume,
} = proxyActivities<typeof activities>({
  startToCloseTimeout: '10 minutes',
  retry: {
    initialInterval: '2 seconds',
    maximumInterval: '30 seconds',
    backoffCoefficient: 2,
    maximumAttempts: 5,
    nonRetryableErrorTypes: ['TerminalPolicyViolationError', 'UnrecoverableASTSyntaxError'],
  },
});

// Signals and Queries
export const humanApprovalSignal = defineSignal<[boolean, string]>('humanApproval');
export const getWorkflowProgressQuery = defineQuery<string>('getProgress');

export interface ReconciliationInput {
  jobId: string;
  repository: string;
  baseBranch: string;
  targetVulnerabilityId: string;
  maxBudgetUsd: number;
  autoMergeAllowed: boolean;
}

export async function AutonomousCodeReconciliationWorkflow(
  input: ReconciliationInput
): Promise<{ prUrl: string; totalSpendUsd: number; status: string }> {
  let progress = 'INITIALIZING';
  let humanApproved: boolean | null = null;
  let approvalReviewer = '';
  let cumulativeSpendUsd = 0;
  let lockLeaseId = '';

  setHandler(getWorkflowProgressQuery, () => `${progress} (Spend: $${cumulativeSpendUsd.toFixed(2)})`);
  setHandler(humanApprovalSignal, (approved, reviewer) => {
    humanApproved = approved;
    approvalReviewer = reviewer;
  });

  // Step 1: Acquire Distributed Git Lock
  progress = 'ACQUIRING_LOCK';
  const lockResult = await acquireDistributedGitLock(input.repository, input.baseBranch);
  if (!lockResult.acquired) {
    throw ApplicationFailure.nonRetryable(
      `Failed to acquire exclusive lock for repository ${input.repository} on ${input.baseBranch}`
    );
  }
  lockLeaseId = lockResult.leaseId;

  try {
    // Step 2: Provision Isolated Cleanroom Workspace
    progress = 'PROVISIONING_WORKSPACE';
    const workspace = await provisionCleanroomVolume(input.jobId, input.repository);

    // Step 3: Autonomous ReAct Reasoning Loop (Max 15 turns)
    progress = 'REASONING_AND_SYNTHESIS';
    let isGoalSatisfied = false;
    let turnCount = 0;

    while (!isGoalSatisfied && turnCount < 15) {
      turnCount++;

      // Check Budget Limit
      if (cumulativeSpendUsd >= input.maxBudgetUsd) {
        throw ApplicationFailure.nonRetryable(
          `Execution aborted: Exceeded maximum allowed budget of $${input.maxBudgetUsd}`
        );
      }

      const turnResult = await executeReActReasoningTurn(
        workspace.path,
        input.targetVulnerabilityId,
        turnCount
      );

      cumulativeSpendUsd += turnResult.turnCostUsd;
      isGoalSatisfied = turnResult.isComplete;
    }

    // Step 4: Run Rigorous Verification Assertions
    progress = 'VERIFYING_TEST_SUITE';
    const testResult = await runAutomatedTestVerification(workspace.path);
    if (!testResult.allTestsPassed) {
      throw ApplicationFailure.nonRetryable(
        `Remediation failed verification: ${testResult.failureSummary}`
      );
    }

    // Step 5: High-Risk Human Review Gate (if breaking changes detected)
    if (!input.autoMergeAllowed || testResult.containsBreakingChanges) {
      progress = 'AWAITING_HUMAN_APPROVAL';
      // Wait up to 24 hours for human sign-off via Slack/Dashboard
      const approvedWithinDeadline = await condition(() => humanApproved !== null, '24 hours');

      if (!approvedWithinDeadline || humanApproved === false) {
        throw ApplicationFailure.nonRetryable(
          `Workflow aborted: Human approval denied or timed out after 24 hours.`
        );
      }
    }

    // Step 6: Create Cryptographic Immutable Audit Block
    progress = 'GENERATING_AUDIT_LEDGER';
    const auditRecord = await createCryptographicAuditBlock(workspace.path, {
      jobId: input.jobId,
      approver: approvalReviewer || 'AUTOMATED_POLICY_GATE',
      totalCost: cumulativeSpendUsd,
      testCoverage: testResult.coveragePercent,
    });

    // Step 7: Dispatch Cryptographically Signed Pull Request
    progress = 'DISPATCHING_PR';
    const prResult = await dispatchSignedPullRequest(workspace.path, {
      repo: input.repository,
      base: input.baseBranch,
      auditHash: auditRecord.sha256,
      title: `[Autonomous Fix] Remediate ${input.targetVulnerabilityId}`,
    });

    progress = 'COMPLETED';
    return {
      prUrl: prResult.prUrl,
      totalSpendUsd: cumulativeSpendUsd,
      status: 'SUCCESS',
    };
  } finally {
    // Step 8: Guaranteed Teardown and Lock Release
    await destroyCleanroomVolume(input.jobId);
    if (lockLeaseId) {
      await releaseDistributedGitLock(input.repository, input.baseBranch, lockLeaseId);
    }
  }
}
