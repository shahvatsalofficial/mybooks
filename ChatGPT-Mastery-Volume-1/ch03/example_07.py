# Aggregate high-volume transactions first (millions of rows -> thousands of customer summaries)
customer_agg = transactions_df.groupby('customer_id').agg(
    lifetime_volume_usd=('amount_usd', 'sum'),
    transaction_count=('amount_usd', 'count'),
    last_active_timestamp=('timestamp', 'max')
).reset_index()

# Downcast foreign keys before join
customer_agg['customer_id'] = pd.to_numeric(customer_agg['customer_id'], downcast='integer')
dim_customers['customer_id'] = pd.to_numeric(dim_customers['customer_id'], downcast='integer')

# Execute clean memory-efficient join on pre-aggregated dimensions
master_customer_report = pd.merge(customer_agg, dim_customers, on='customer_id', how='left')
print(f"Joined {len(master_customer_report):,} consolidated customer profiles safely within memory limits.")
