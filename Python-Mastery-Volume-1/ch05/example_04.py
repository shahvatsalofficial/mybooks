# ANTI-PATTERN: Default chunksize=1
results = list(executor.map(calculate_risk, trades, chunksize=1))
