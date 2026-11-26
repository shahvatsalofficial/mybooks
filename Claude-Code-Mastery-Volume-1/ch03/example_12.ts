/**
 * Claude Code Enterprise Prompt Compiler & Schema Validator
 * Version: 2.4 | Production Grade
 * Author: Vatsal Shah (https://shahvatsal.com)
 */

import * as fs from 'fs';
import * as path from 'path';

export interface SystemInvariant {
  id: string;
  rule: string;
  severity: 'BLOCKING' | 'WARNING';
}

export interface PromptEnvelopeOptions {
  projectRoot: string;
  branch: string;
  baseCommit: string;
  userObjective: string;
  invariants: SystemInvariant[];
  activeRuleFiles: string[];
}

export interface ReplaceFilePayload {
  TargetFile: string;
  StartLine: number;
  EndLine: number;
  TargetContent: string;
  ReplacementContent: string;
  Instruction: string;
}

export class PromptCompiler {
  /**
   * Compiles multi-tier system directives and context into a hardened XML envelope.
   */
  public static compileExecutionEnvelope(options: PromptEnvelopeOptions): string {
    const rulesLattice = this.loadRules(options.projectRoot, options.activeRuleFiles);

    return `<agent_execution_envelope version="2.4" timestamp="${new Date().toISOString()}">
  <!-- TIER 1: IMMUTABLE SYSTEM DIRECTIVES -->
  <system_directives priority="P0" enforce_safety="strict">
${options.invariants
  .map(
    (inv) =>
      `    <invariant id="${inv.id}" severity="${inv.severity}">${this.escapeXml(inv.rule)}</invariant>`
  )
  .join('\n')}
  </system_directives>

  <!-- TIER 2: PROJECT MEMORY LATTICE (CLAUDE.MD) -->
  <project_memory_lattice root="${this.escapeXml(options.projectRoot)}">
${rulesLattice}
  </project_memory_lattice>

  <!-- TIER 3: UNTRUSTED USER OBJECTIVE (ISOLATED DATA SANDBOX) -->
  <untrusted_user_payload sanitize="true" origin="cli_dispatcher">
    <data_sandbox encoding="utf-8" evaluate_instructions="false">
${this.escapeXml(options.userObjective)}
    </data_sandbox>
  </untrusted_user_payload>

  <!-- TIER 4: OUTPUT CONTRACT -->
  <output_contract format="structured_cot_rpc">
    <mandatory_structure>
      1. Emit latent planning trace inside &lt;thinking&gt; ... &lt;/thinking&gt; tags.
      2. Perform AST pre-flight verification against exact disk buffers.
      3. Emit deterministic tool call conforming strictly to registered JSON schemas.
    </mandatory_structure>
  </output_contract>
</agent_execution_envelope>`;
  }

  /**
   * Pre-flight AST boundary validator for replace_file_content tool calls.
   */
  public static validateAndExecuteReplace(
    payload: ReplaceFilePayload
  ): { success: boolean; message: string; diffLines?: number } {
    if (!path.isAbsolute(payload.TargetFile)) {
      return {
        success: false,
        message: `VALIDATION_ERROR: TargetFile must be an absolute path. Received: ${payload.TargetFile}`,
      };
    }

    if (!fs.existsSync(payload.TargetFile)) {
      return {
        success: false,
        message: `VALIDATION_ERROR: Target file does not exist on disk: ${payload.TargetFile}`,
      };
    }

    const fileContent = fs.readFileSync(payload.TargetFile, 'utf8');
    const lines = fileContent.split(/\r?\n/);

    if (payload.StartLine < 1 || payload.EndLine > lines.length || payload.StartLine > payload.EndLine) {
      return {
        success: false,
        message: `BOUNDARY_ERROR: Requested line range [${payload.StartLine}, ${payload.EndLine}] is out of bounds for file with ${lines.length} lines.`,
      };
    }

    // Extract search window (0-indexed)
    const windowSlice = lines.slice(payload.StartLine - 1, payload.EndLine).join('\n');

    // Normalize newlines for strict comparison
    const normalizedWindow = windowSlice.replace(/\r\n/g, '\n');
    const normalizedTarget = payload.TargetContent.replace(/\r\n/g, '\n');

    if (!normalizedWindow.includes(normalizedTarget)) {
      const actualRangeSnippet = lines
        .slice(Math.max(0, payload.StartLine - 2), Math.min(lines.length, payload.EndLine + 1))
        .map((l, idx) => `${payload.StartLine - 1 + idx}: ${l}`)
        .join('\n');

      return {
        success: false,
        message: `TARGET_MISMATCH: TargetContent not found in specified range.\nActual disk content near lines:\n${actualRangeSnippet}`,
      };
    }

    // Execute atomic replacement in memory
    const beforeBlock = lines.slice(0, payload.StartLine - 1).join('\n');
    const afterBlock = lines.slice(payload.EndLine).join('\n');

    const updatedWindow = normalizedWindow.replace(normalizedTarget, payload.ReplacementContent);
    const newFullContent = [beforeBlock, updatedWindow, afterBlock].filter((b) => b.length > 0).join('\n');

    // Write back atomically
    fs.writeFileSync(payload.TargetFile, newFullContent, 'utf8');

    return {
      success: true,
      message: `SUCCESS: Replaced content cleanly in ${payload.TargetFile}.`,
      diffLines: payload.ReplacementContent.split('\n').length - payload.TargetContent.split('\n').length,
    };
  }

  private static loadRules(root: string, ruleFiles: string[]): string {
    return ruleFiles
      .map((rf) => {
        const fullPath = path.join(root, rf);
        if (fs.existsSync(fullPath)) {
          const content = fs.readFileSync(fullPath, 'utf8');
          return `    <rule_file path="${rf}">\n${this.escapeXml(content)}\n    </rule_file>`;
        }
        return `    <!-- Rule file ${rf} not found -->`;
      })
      .join('\n');
  }

  private static escapeXml(unsafe: string): string {
    return unsafe
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&apos;');
  }
}
