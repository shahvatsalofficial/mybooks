# Worker memory containment configuration
app.conf.update(
    # Terminate and spawn a fresh child worker process after executing 500 tasks
    worker_max_tasks_per_child=500,
    
    # Automatically recycle a worker process if its resident memory exceeds 350 MB
    worker_max_memory_per_child=350000,  # 350,000 KB (~350 MB)
)
