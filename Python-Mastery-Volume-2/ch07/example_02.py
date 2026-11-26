import mmap

# Instruct Linux kernel to optimize page loading:
# MADV_SEQUENTIAL: Expect sequential page access; doubles OS read-ahead buffer depth
mm.madvise(mmap.MADV_SEQUENTIAL)

# MADV_WILLNEED: Proactively pre-loads pages from NVMe into page cache in background
mm.madvise(mmap.MADV_WILLNEED)
