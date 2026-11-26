# Configure fair task distribution for long-running or heterogeneous tasks
app.conf.update(
    worker_prefetch_multiplier=1,  # Worker pulls exactly 1 task at a time
    task_acks_late=True,          # Acknowledge task only AFTER completion
    task_reject_on_worker_lost=True, # Requeue task if worker process dies abruptly
)
