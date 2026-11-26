import pandas as pd
from collections import defaultdict

mcc_totals = defaultdict(float)
mcc_fraud = defaultdict(float)

# Process in stream chunks of 100,000 rows
for chunk in pd.read_csv('/mnt/data/transactions_10m.csv', chunksize=100_000, usecols=['mcc', 'amount', 'is_fraud']):
    for mcc, group in chunk.groupby('mcc'):
        mcc_totals[mcc] += group['amount'].sum()
        mcc_fraud[mcc] += group[group['is_fraud'] == 1]['amount'].sum()

summary_records = []
for mcc in mcc_totals:
    total = mcc_totals[mcc]
    fraud = mcc_fraud[mcc]
    rate = (fraud / total) * 100 if total > 0 else 0.0
    summary_records.append({'mcc': mcc, 'total_volume_usd': total, 'fraud_volume_usd': fraud, 'fraud_rate_pct': rate})

result_df = pd.DataFrame(summary_records).sort_values(by='fraud_volume_usd', ascending=False)
result_df.to_csv('/mnt/data/mcc_fraud_summary.csv', index=False)
print("10M row processing completed without memory overflow.")
