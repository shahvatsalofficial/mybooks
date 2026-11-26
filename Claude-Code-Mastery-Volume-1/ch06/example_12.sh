# SRE Emergency Branch Recovery Script
git log -g --abbrev-commit --pretty=oneline | grep "checkout: moving from" | head -n 20
