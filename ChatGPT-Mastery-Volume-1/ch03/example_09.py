import pandas as pd

# Creating a multi-tab enterprise audit workbook
with pd.ExcelWriter('/mnt/data/quarterly_audit_master.xlsx', engine='openpyxl') as writer:
    summary_df.to_excel(writer, sheet_name='Executive Summary', index=False)
    departmental_df.to_excel(writer, sheet_name='Departmental Breakdown', index=False)
    raw_anomalies_df.to_excel(writer, sheet_name='Flagged Anomalies', index=False)

print("Master audit workbook compiled successfully. Download link ready at /mnt/data/quarterly_audit_master.xlsx")
