for col in df.select_dtypes(include=['object']).columns:
    num_unique = df[col].nunique()
    num_total = len(df[col])
    # If cardinality ratio is under 50%, convert to category
    if num_unique / num_total < 0.5:
        df[col] = df[col].astype('category')
