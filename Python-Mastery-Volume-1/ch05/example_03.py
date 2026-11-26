import numpy as np

# Create a 100,000,000 element float64 array directly inside shared RAM
shared_array = np.ndarray((100_000_000,), dtype=np.float64, buffer=shm.buf)
