# Execute test suite across 8 parallel worker processes
pytest -n 8 --dist=loadgroup
