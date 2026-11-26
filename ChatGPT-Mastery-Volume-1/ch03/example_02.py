import pandas as pd
import numpy as np

def downcast_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Downcasts numerical columns to the smallest feasible precision."""
    for col in df.select_dtypes(include=['int']).columns:
        df[col] = pd.to_numeric(df[col], downcast='integer')
    for col in df.select_dtypes(include=['float']).columns:
        df[col] = pd.to_numeric(df[col], downcast='float')
    return df
