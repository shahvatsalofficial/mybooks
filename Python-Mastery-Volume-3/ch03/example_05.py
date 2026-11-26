# tasks/workflows.py
"""Distributed batch processing workflows using Celery Canvas chords and groups."""

from __future__ import annotations
from decimal import Decimal
import logging
import time
from celery import Celery, chord, group

# Configure Celery application with resilient broker settings
celery_app = Celery("enterprise_workflows")
celery_app.conf.update(
    broker_url="redis://localhost:6379/0",
    result_backend="redis://localhost:6379/1",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    worker_prefetch_multiplier=1,  # Fair task scheduling
    task_acks_late=True,          # Late acknowledgment
    task_track_started=True,
)

logger = logging.getLogger("celery_tasks")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def process_customer_statement(self, customer_id: str, statement_period: str) -> dict[str, Any]:
    """Processes an individual customer billing statement calculation."""
    logger.info("Computing statement for customer=%s period=%s", customer_id, statement_period)
    try:
        # Simulate computational processing
        total_charges = Decimal("450.75")
        tax = total_charges * Decimal("0.08")
        return {
            "customer_id": customer_id,
            "period": statement_period,
            "subtotal": float(total_charges),
            "tax": float(tax),
            "total": float(total_charges + tax),
            "status": "PROCESSED",
        }
    except Exception as exc:
        logger.exception("Failed calculating statement for customer=%s", customer_id)
        raise self.retry(exc=exc)


@celery_app.task
def finalize_batch_statement_run(results: list[dict[str, Any]], batch_id: str) -> dict[str, Any]:
    """Chord callback executing only after ALL parallel statement tasks have finished."""
    total_processed = len(results)
    aggregate_revenue = sum(r["total"] for r in results)
    
    logger.info(
        "BATCH FINISHED [ID=%s]: Successfully processed %d statements. Total Revenue: $%.2f",
        batch_id,
        total_processed,
        aggregate_revenue,
    )

    return {
        "batch_id": batch_id,
        "total_statements": total_processed,
        "aggregate_revenue": aggregate_revenue,
        "completion_timestamp": time.time(),
    }


def dispatch_enterprise_billing_workflow(customer_ids: list[str], period: str, batch_id: str) -> None:
    """Dispatches a synchronized Celery Chord executing statements in parallel with a final barrier."""
    logger.info("Dispatching parallel statement calculation for %d customers...", len(customer_ids))

    # Construct parallel group of task signatures
    header = group(process_customer_statement.s(cid, period) for cid in customer_ids)
    
    # Construct final barrier callback signature
    callback = finalize_batch_statement_run.s(batch_id=batch_id)

    # Execute distributed Chord
    workflow = chord(header)(callback)
    logger.info("Chord workflow initiated successfully. Task ID: %s", workflow.id)
