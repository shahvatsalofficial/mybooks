# Pipelining static analysis diagnostics directly into Claude Code for autonomous triage
cargo clippy --message-format=json | jq -r '.message' | claude -p "Fix the high-severity warnings"

# Chaining Git inspection with automated commit message synthesis
git diff --staged | claude -p "Generate a conventional commit message adhering to repository standards"
