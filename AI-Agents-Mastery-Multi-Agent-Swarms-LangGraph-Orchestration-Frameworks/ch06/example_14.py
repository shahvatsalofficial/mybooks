class QueueTelemetryExporter:
    def __init__(self, queue_name: str):
        self.queue_name = queue_name

    def export_metrics(self, current_depth: int) -> str:
        return (
            f"# HELP amqp_queue_depth Current messages pending in queue\n"
            f"# TYPE amqp_queue_depth gauge\n"
            f'amqp_queue_depth{{queue="{self.queue_name}"}} {current_depth}\n'
        )
