async def orchestrate_payment_pipeline():
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(fetch_pricing())
            tg.create_task(charge_card())
            tg.create_task(notify_warehouse())
    except* TimeoutError as eg:
        # Handles all TimeoutErrors across any child task
        logger.error(f"Network timeout encountered: {eg.exceptions}")
    except* PaymentDeclinedError as eg:
        # Handles payment business failure
        logger.warning(f"Card authorization rejected: {eg.exceptions}")
    except* Exception as eg:
        # Catches all remaining uncaught exceptions
        logger.critical(f"Catastrophic pipeline failure: {eg.exceptions}")
