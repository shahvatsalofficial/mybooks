import os
import pandas as pd

COLUMN_ALIAS_MAP = {
    'client_id': 'user_id',
    'customer_id': 'user_id',
    'trans_date': 'timestamp',
    'transaction_time': 'timestamp',
    'amt': 'amount',
    'txn_amount': 'amount'
}

STANDARD_COLUMNS = ['user_id', 'timestamp', 'amount']
merged_dfs = []

batch_dir = '/mnt/data/raw_batches/'
for fname in os.listdir(batch_dir):
    if fname.endswith('.csv'):
        fpath = os.path.join(batch_dir, fname)
        df_batch = pd.read_csv(fpath)
        # Rename columns using alias map
        df_batch.rename(columns=COLUMN_ALIAS_MAP, inplace=True)
        # Filter down strictly to standardized schema
        available_cols = [c for c in STANDARD_COLUMNS if c in df_batch.columns]
        df_batch = df_batch[available_cols]
        merged_dfs.append(df_batch)

final_df = pd.concat(merged_dfs, ignore_index=True)
print(f"Successfully consolidated {len(merged_dfs)} heterogeneous files into {len(final_df):,} standard records.")
