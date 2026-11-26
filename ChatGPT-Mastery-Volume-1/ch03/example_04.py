chunk_size = 50_000
running_revenue = 0.0
total_transactions = 0

for chunk in pd.read_csv('/mnt/data/large_dataset.csv', chunksize=chunk_size, usecols=['revenue', 'status']):
    completed = chunk[chunk['status'] == 'COMPLETED']
    running_revenue += completed['revenue'].sum()
    total_transactions += len(completed)

mean_revenue = running_revenue / total_transactions if total_transactions else 0.0
print(f"Total Transactions: {total_transactions:,} | Mean Revenue: ${mean_revenue:,.2f}")
