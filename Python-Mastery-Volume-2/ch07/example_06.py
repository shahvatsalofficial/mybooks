# CATASTROPHIC FLAW IN v3.9.0 PRODUCTION CODE:
def normalize_feature_matrix(matrix: np.ndarray, column_indices: list[int]) -> np.ndarray:
    # Intended to extract a subset of columns for inference:
    # FLAW: Passing a list of integers triggers NUMPY ADVANCED INDEXING!
    # Advanced indexing FORCES A COMPLETE DEEP MEMORY COPY of the entire matrix!
    sub_matrix = matrix[:, column_indices]  # Allocates and copies 1.2 GB per tick!
    return sub_matrix - np.mean(sub_matrix, axis=0)
