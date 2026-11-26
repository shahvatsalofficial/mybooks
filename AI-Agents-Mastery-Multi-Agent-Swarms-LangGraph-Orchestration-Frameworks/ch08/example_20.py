GITHUB_ACTIONS_WORKFLOW_YAML = """
name: Multi-Agent Swarm CI Regression
on: [push, pull_request]
jobs:
  agent-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - name: Run Trajectory Evals
        run: pytest tests/test_swarm_regressions.py --maxfail=1
"""
