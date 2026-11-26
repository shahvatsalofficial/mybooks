import numpy as np
from statsmodels.stats.multitest import multipletests

raw_p_values = [0.002, 0.012, 0.045, 0.068, 0.120, 0.230, 0.034, 0.540, 0.890, 0.049]
reject, corrected_p_vals, _, _ = multipletests(raw_p_values, alpha=0.05, method='fdr_bh')

for i, (orig, corr, rej) in enumerate(zip(raw_p_values, corrected_p_vals, reject)):
    print(f"Hypothesis {i+1:02d}: Raw p = {orig:.4f} -> Corrected p = {corr:.4f} | Statistically Significant: {rej}")
