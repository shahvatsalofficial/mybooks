def error_classification_pipeline(eg: ExceptionGroup) -> None:
    # Extract only network-related exceptions using a predicate
    transient_group, fatal_group = eg.split(
        lambda e: isinstance(e, (ConnectionError, TimeoutError, OSError))
    )
    
    if transient_group is not None:
        logger.info("Found transient errors capable of safe retry:")
        for exc in transient_group.exceptions:
            logger.info(f"  -> {type(exc).__name__}: {exc}")
            
    if fatal_group is not None:
        logger.critical("Found non-recoverable fatal errors requiring operator intervention:")
        for exc in fatal_group.exceptions:
            logger.critical(f"  -> {type(exc).__name__}: {exc}")
        # Re-raise the unrecoverable portion
        raise fatal_group
