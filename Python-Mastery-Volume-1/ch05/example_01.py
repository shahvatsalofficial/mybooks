from multiprocessing.shared_memory import SharedMemory

# Allocates 1GB of physical RAM in the OS shared memory pool
shm = SharedMemory(name="psm_market_data", create=True, size=1024 * 1024 * 1024)
