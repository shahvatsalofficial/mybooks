# DEFECTIVE PRODUCTION CODE (Pre-Incident)
def spawn_pricing_engine():
    # Defect 1: Implicitly used default 'fork' on Linux
    p = mp.Process(target=worker_pricing_loop, args=(market_queue,))
    p.start()
