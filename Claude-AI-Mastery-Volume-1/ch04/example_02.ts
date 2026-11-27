/**
 * Enterprise Claude Artifact Git Exporter & PR Automation
 * Author: Vatsal Shah, Lead Enterprise AI Architect
 * Publisher: Vatsal Shah (c) 2026
 */

import { Octokit } from '@octokit/rest';
import express, { Request, Response } from 'express';

const app = express();
app.use(express.json());

const octokit = new Octokit({ auth: process.env.GITHUB_PERSONAL_ACCESS_TOKEN });
const REPO_OWNER = 'enterprise-org';
const REPO_NAME = 'core-frontend-app';

interface ArtifactDeploymentPayload {
  artifactId: string;
  componentName: string;
  sourceCode: string;
  targetDirectory: string;
  authorEmail: string;
}

app.post('/v1/artifacts/publish', async (req: Request, res: Response) => {
  const payload: ArtifactDeploymentPayload = req.body;
  const branchName = `claude-artifact-${payload.artifactId.toLowerCase()}-${Date.now()}`;
  const filePath = `src/components/${payload.targetDirectory}/${payload.componentName}.tsx`;

  console.log(`[ArtifactPublisher] Received publishing request for ${payload.componentName}...`);

  try {
    // 1. Get default branch commit SHA
    const { data: refData } = await octokit.git.getRef({
      owner: REPO_OWNER,
      repo: REPO_NAME,
      ref: 'heads/main'
    });
    const mainSha = refData.object.sha;

    // 2. Create new feature branch
    await octokit.git.createRef({
      owner: REPO_OWNER,
      repo: REPO_NAME,
      ref: `refs/heads/${branchName}`,
      sha: mainSha
    });
    console.log(`  -> Created branch: ${branchName}`);

    // 3. Commit artifact source code
    await octokit.repos.createOrUpdateFileContents({
      owner: REPO_OWNER,
      repo: REPO_NAME,
      path: filePath,
      message: `feat(ui): add ${payload.componentName} generated via Claude Artifact`,
      content: Buffer.from(payload.sourceCode).toString('base64'),
      branch: branchName
    });
    console.log(`  -> Committed file: ${filePath}`);

    // 4. Open automated Pull Request
    const { data: prData } = await octokit.pulls.create({
      owner: REPO_OWNER,
      repo: REPO_NAME,
      title: `[AI Artifact] Add ${payload.componentName} Component`,
      head: branchName,
      base: 'main',
      body: `### Automated Claude Artifact Deployment\n\n- **Artifact ID**: `${payload.artifactId}`\n- **Target File**: `${filePath}`\n- **Author**: ${payload.authorEmail}\n\n*Review component code and automated unit tests before merging.*`,
      maintainer_can_modify: true
    });

    console.log(`✅ Pull Request opened successfully: ${prData.html_url}`);
    return res.status(200).json({ status: 'PR_OPENED', prUrl: prData.html_url });

  } catch (error: any) {
    console.error('[ArtifactPublisher] Fatal error during deployment:', error.message);
    return res.status(500).json({ error: error.message });
  }
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`Artifact Publisher running on port ${PORT}`));
