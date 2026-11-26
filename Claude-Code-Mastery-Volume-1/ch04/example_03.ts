import { TerminalWorkflowOrchestrator, RefactorDAGNode } from './TerminalWorkflowOrchestrator';
import * as child_process from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import * as assert from 'assert';

describe('TerminalWorkflowOrchestrator Integration Test Suite', () => {
  const repoDir = path.join(__dirname, 'test_repo_workspace');

  beforeEach(() => {
    if (!fs.existsSync(repoDir)) fs.mkdirSync(repoDir, { recursive: true });
    // Initialize test git repository
    child_process.execSync('git init', { cwd: repoDir });
    child_process.execSync('git config user.name "Authorizer"', { cwd: repoDir });
    child_process.execSync('git config user.email "auth@enterprise.com"', { cwd: repoDir });

    fs.writeFileSync(path.join(repoDir, 'moduleA.ts'), 'export const VERSION = 1;\n', 'utf8');
    fs.writeFileSync(path.join(repoDir, 'moduleB.ts'), "import { VERSION } from './moduleA';\n", 'utf8');

    child_process.execSync('git add -A && git commit -m "chore: initial commit"', { cwd: repoDir });
  });

  afterEach(() => {
    if (fs.existsSync(repoDir)) fs.rmSync(repoDir, { recursive: true, force: true });
  });

  it('should execute a clean multi-file atomic DAG update when verification passes', () => {
    const orchestrator = new TerminalWorkflowOrchestrator(repoDir);
    const dag: RefactorDAGNode[] = [
      {
        file: 'moduleA.ts',
        dependencies: [],
        mutations: [
          {
            filePath: 'moduleA.ts',
            startLine: 1,
            endLine: 1,
            targetContent: 'export const VERSION = 1;',
            replacementContent: 'export const VERSION = 2;',
          },
        ],
      },
      {
        file: 'moduleB.ts',
        dependencies: ['moduleA.ts'],
        mutations: [
          {
            filePath: 'moduleB.ts',
            startLine: 1,
            endLine: 1,
            targetContent: "import { VERSION } from './moduleA';",
            replacementContent: "import { VERSION } from './moduleA';\nconsole.log(VERSION);",
          },
        ],
      },
    ];

    const result = orchestrator.executeAtomicRefactoring(dag, 'node -e "process.exit(0)"');
    assert.strictEqual(result.success, true);

    const updatedA = fs.readFileSync(path.join(repoDir, 'moduleA.ts'), 'utf8');
    assert.ok(updatedA.includes('VERSION = 2;'));
  });

  it('should trigger automatic rollback and leave workspace clean when verification gate fails', () => {
    const orchestrator = new TerminalWorkflowOrchestrator(repoDir);
    const dag: RefactorDAGNode[] = [
      {
        file: 'moduleA.ts',
        dependencies: [],
        mutations: [
          {
            filePath: 'moduleA.ts',
            startLine: 1,
            endLine: 1,
            targetContent: 'export const VERSION = 1;',
            replacementContent: 'export const BROKEN_VERSION = null;',
          },
        ],
      },
    ];

    // Verification command deliberately exits with 1
    const result = orchestrator.executeAtomicRefactoring(dag, 'node -e "process.exit(1)"');
    assert.strictEqual(result.success, false);
    assert.ok(result.message.includes('VERIFICATION_FAILED'));

    // Assert that moduleA was rolled back to pristine state
    const restoredA = fs.readFileSync(path.join(repoDir, 'moduleA.ts'), 'utf8');
    assert.ok(restoredA.includes('VERSION = 1;'));
  });
});
