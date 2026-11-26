/**
 * scripts/validate-claude-rules.js
 * Sovereign CI verification script for Claude Code memory files.
 * Enforces frontmatter compliance, token ceilings, and formatting standards.
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

const MAX_RULE_TOKENS = 1500;
const REPO_ROOT = path.resolve(__dirname, '..');
const RULES_DIR = path.join(REPO_ROOT, '.claude', 'rules');

function estimateTokenCount(text) {
  // Conservative heuristic: ~4 characters per token for technical English
  return Math.ceil(text.length / 3.8);
}

function parseFrontmatter(content) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return { frontmatter: null, body: content };
  
  const yamlBlock = match[1];
  const body = content.slice(match[0].length);
  const metadata = {};
  
  yamlBlock.split('\n').forEach(line => {
    const [key, ...values] = line.split(':');
    if (key && values.length) {
      metadata[key.trim()] = values.join(':').trim();
    }
  });
  
  return { frontmatter: metadata, body };
}

function validateRules() {
  console.log('🔍 Auditing Claude Code Memory Architecture...');
  let hasErrors = false;

  // 1. Audit Root CLAUDE.md
  const rootClaudePath = path.join(REPO_ROOT, 'CLAUDE.md');
  if (!fs.existsSync(rootClaudePath)) {
    console.error('❌ FATAL: Root CLAUDE.md is missing from repository root.');
    hasErrors = true;
  } else {
    const rootContent = fs.readFileSync(rootClaudePath, 'utf8');
    const rootTokens = estimateTokenCount(rootContent);
    console.log(`✅ Root CLAUDE.md located (${rootTokens} estimated tokens).`);
    if (rootTokens > 3000) {
      console.warn(`⚠️ WARNING: Root CLAUDE.md exceeds 3,000 tokens (${rootTokens}). Consider decomposing into .claude/rules/.`);
    }
  }

  // 2. Audit .claude/rules/*.md
  if (fs.existsSync(RULES_DIR)) {
    const ruleFiles = glob.sync('**/*.md', { cwd: RULES_DIR, absolute: true });
    
    ruleFiles.forEach(filePath => {
      const relPath = path.relative(REPO_ROOT, filePath);
      const content = fs.readFileSync(filePath, 'utf8');
      const { frontmatter, body } = parseFrontmatter(content);
      const tokens = estimateTokenCount(content);

      console.log(`Checking rule: ${relPath} (~${tokens} tokens)`);

      // Verify token ceiling
      if (tokens > MAX_RULE_TOKENS) {
        console.error(`❌ [${relPath}]: Exceeds maximum token ceiling of ${MAX_RULE_TOKENS} (Found ~${tokens}).`);
        hasErrors = true;
      }

      // Verify frontmatter existence and description
      if (!frontmatter || !frontmatter.description) {
        console.error(`❌ [${relPath}]: Missing required YAML frontmatter with 'description' field.`);
        hasErrors = true;
      }

      // Verify heading structure
      if (!body.includes('# ')) {
        console.error(`❌ [${relPath}]: Rule body must contain at least one Level 1 heading (#).`);
        hasErrors = true;
      }
    });
  }

  if (hasErrors) {
    console.error('\n💥 Memory audit failed. Fix the errors above before merging.');
    process.exit(1);
  } else {
    console.log('\n✨ All Claude Code memory specifications passed verification.');
  }
}

validateRules();
