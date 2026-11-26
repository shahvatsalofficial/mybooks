async def execute_enterprise_resilient_batch(payloads: list[dict]) -> None:
    try:
        async with asyncio.TaskGroup() as tg:
            for item in payloads:
                tg.create_task(process_telemetry_item(item))
    except* ConnectionError as eg:
        # eg is an ExceptionGroup containing ONLY the ConnectionError leaves
        logger.warning(f"Trapped {len(eg.exceptions)} connection drops. Initiating backoff retry...")
        await schedule_exponential_retry(eg.exceptions)
    except* ValueError as eg:
        # eg is an ExceptionGroup containing ONLY the ValueError leaves
        logger.error(f"Quarantining {len(eg.exceptions)} corrupted payloads to Dead-Letter Queue.")
        for err in eg.exceptions:
            await dead_letter_queue.publish(err)
    except* KeyError as eg:
        # eg contains ONLY KeyError leaves
        logger.critical(f"Schema mismatch detected: {eg.exceptions}")
        metrics.increment("schema.mismatch.fatal")
