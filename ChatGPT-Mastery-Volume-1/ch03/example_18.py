import os
import pdfplumber
import pandas as pd
import re

audit_rows = []
invoice_dir = '/mnt/data/invoices/'

for fname in os.listdir(invoice_dir):
    if fname.endswith('.pdf'):
        pdf_path = os.path.join(invoice_dir, fname)
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() or ""
                # Extract tables using precision line bounding
                tables = page.extract_tables()
                for table in tables:
                    for row in table[1:]: # Skip header
                        if len(row) >= 4 and row[0]:
                            item_desc, qty, unit_price, total_str = row[0], row[1], row[2], row[3]
                            try:
                                q_val = float(qty)
                                p_val = float(re.sub(r'[^\d.]', '', unit_price))
                                calc_total = q_val * p_val
                                audit_rows.append({
                                    'invoice_file': fname,
                                    'item': item_desc,
                                    'quantity': q_val,
                                    'unit_price': p_val,
                                    'calculated_total': calc_total
                                })
                            except (ValueError, TypeError):
                                continue

audit_df = pd.DataFrame(audit_rows)
audit_df.to_csv('/mnt/data/consolidated_invoice_audit.csv', index=False)
print(f"Extracted {len(audit_df):,} line items across PDF invoice collection.")
