import { Octokit } from "@octokit/rest";

const octokit = new Octokit({ auth: process.env.GITHUB_TOKEN });

export async function dispatchWorkflowAndWait(
  owner: string,
  repo: string,
  workflowId: string,
  ref: string,
  inputs: Record<string, any>
): Promise<string> {
  // 1. Dispatch workflow
  await octokit.rest.actions.createWorkflowDispatch({
    owner,
    repo,
    workflow_id: workflowId,
    ref,
    inputs
  });

  // 2. Poll for the triggered run
  let runId: number | null = null;
  for (let attempt = 0; attempt < 10; attempt++) {
    await new Promise((r) => setTimeout(r, 2000));
    const runs = await octokit.rest.actions.listWorkflowRuns({
      owner,
      repo,
      workflow_id: workflowId,
      per_page: 5
    });
    const latest = runs.data.workflow_runs[0];
    if (latest && (latest.status === "queued" || latest.status === "in_progress")) {
      runId = latest.id;
      break;
    }
  }

  if (!runId) throw new Error("Timeout waiting for workflow run initialization.");
  return `Workflow dispatched successfully. Run ID: ${runId}`;
}
