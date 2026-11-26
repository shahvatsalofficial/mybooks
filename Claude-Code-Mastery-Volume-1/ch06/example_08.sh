cosign sign-blob --key cosign.key .claude/skills/refactor_auth/SKILL.md
  ```
- The resulting signature is stored alongside the bundle as `SKILL.md.sig`.
- When the agent router discovers a skill during startup, it validates the cryptographic signature against the enterprise public key infrastructure (PKI).
- If the signature is missing, expired, or invalid due to a single altered byte in the script, the router quarantines the skill, blocks execution, and triggers a security incident alert.

---

## 7. Production TypeScript Implementation: Custom Slash Command Router & AST Dispatcher

The following production-grade TypeScript implementation demonstrates a complete, battle-tested **Slash Command Router & AST Dispatcher**. It incorporates multi-tier directory resolution, lexical argument tokenization, YAML frontmatter parsing, shell injection sanitization, and sandboxed execution.
