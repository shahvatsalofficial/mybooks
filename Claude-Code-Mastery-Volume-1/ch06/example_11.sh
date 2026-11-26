# FLAWED PRUNING SCRIPT (prune.sh)
for branch in $(git branch -r --merged origin/main); do
    # Strip origin/ prefix naively
    clean_branch=${branch#origin/}
    # FATAL: If clean_branch contains a slash, regex match fails open!
    if [[ "$clean_branch" =~ $EXCLUDE_PATTERN ]]; then
        echo "Skipping $clean_branch"
    else
        git push origin --delete "$clean_branch"
    fi
done
