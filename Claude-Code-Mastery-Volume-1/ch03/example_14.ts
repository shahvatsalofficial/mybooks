import { PromptCompiler, ReplaceFilePayload } from './PromptCompiler';
import * as fs from 'fs';
import * as path from 'path';
import * as assert from 'assert';

describe('PromptCompiler & AST Boundary Suite', () => {
  const testDir = path.join(__dirname, 'test_scratch');
  const sampleFile = path.join(testDir, 'sample_auth.ts');

  beforeEach(() => {
    if (!fs.existsSync(testDir)) fs.mkdirSync(testDir, { recursive: true });
    fs.writeFileSync(
      sampleFile,
      `import { verify } from 'jsonwebtoken';\n\nexport function checkToken(t: string): boolean {\n  return verify(t, 'secret') !== null;\n}\n`,
      'utf8'
    );
  });

  afterEach(() => {
    if (fs.existsSync(testDir)) fs.rmSync(testDir, { recursive: true, force: true });
  });

  it('should compile an XML envelope with complete entity escaping', () => {
    const envelope = PromptCompiler.compileExecutionEnvelope({
      projectRoot: testDir,
      branch: 'main',
      baseCommit: 'a1b2c3d',
      userObjective: 'Refactor checkToken to support <RSA_2048> & "HS256"',
      invariants: [{ id: 'INV-1', rule: 'Must sanitize input & prevent injections', severity: 'BLOCKING' }],
      activeRuleFiles: [],
    });

    assert.ok(envelope.includes('&lt;RSA_2048&gt; &amp; &quot;HS256&quot;'));
    assert.ok(envelope.includes('&amp; prevent injections'));
    assert.ok(envelope.includes('<system_directives priority="P0" enforce_safety="strict">'));
  });

  it('should execute a clean atomic replacement when AST anchors match', () => {
    const payload: ReplaceFilePayload = {
      TargetFile: sampleFile,
      StartLine: 3,
      EndLine: 5,
      TargetContent: `export function checkToken(t: string): boolean {\n  return verify(t, 'secret') !== null;\n}`,
      ReplacementContent: `export function checkToken(t: string, key: string): boolean {\n  return verify(t, key) !== null;\n}`,
      Instruction: 'Add key parameter to checkToken signature',
    };

    const result = PromptCompiler.validateAndExecuteReplace(payload);
    assert.strictEqual(result.success, true);

    const updated = fs.readFileSync(sampleFile, 'utf8');
    assert.ok(updated.includes('checkToken(t: string, key: string): boolean'));
  });

  it('should reject replacement and return diagnostic snippet on content mismatch', () => {
    const payload: ReplaceFilePayload = {
      TargetFile: sampleFile,
      StartLine: 3,
      EndLine: 5,
      TargetContent: `export function nonExistentFunction(): void {}`,
      ReplacementContent: `export function replacement(): void {}`,
      Instruction: 'Invalid target mutation',
    };

    const result = PromptCompiler.validateAndExecuteReplace(payload);
    assert.strictEqual(result.success, false);
    assert.ok(result.message.includes('TARGET_MISMATCH'));
  });
});
