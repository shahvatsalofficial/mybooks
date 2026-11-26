# Production Prefork Initialization Hook (gunicorn.conf.py):
import gc

def on_starting(server):
    """Executes in master process before forking workers."""
    # 1. Warm all application caches and import all modules
    preload_application_code()
    
    # 2. Collect all transient setup garbage
    gc.collect()
    
    # 3. Freeze all static memory into permanent, non-GC tracked COW pages
    gc.freeze()
    print("Application memory frozen. Forking child worker processes...")
