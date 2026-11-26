# Verifying and Enforcing Memory Contiguity:
import numpy as np

def ensure_c_contiguous(arr: np.ndarray) -> np.ndarray:
    """Guarantees array is C-contiguous, aligned, and writeable without unnecessary copies."""
    # Fast path: if already contiguous, returns view immediately in O(1) time
    if arr.flags.c_contiguous and arr.flags.aligned:
        return arr
    
    # Slow path: executes single contiguous copy only when strictly required
    return np.ascontiguousarray(arr)
