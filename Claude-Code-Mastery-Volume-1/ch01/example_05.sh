# Claude Code internal pre-flight snapshot harness
git rev-parse --is-inside-work-tree >/dev/null 2>&1
CURRENT_SHA=$(git rev-parse HEAD)
DIRTY_FILES=$(git status --porcelain)

if [ -n "$DIRTY_FILES" ]; then
    # Create an ephemeral shadow stash without altering developer working tree
    git stash create > /tmp/claude_shadow_ref
fi
