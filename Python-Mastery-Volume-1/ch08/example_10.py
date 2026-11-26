from contextlib import AsyncExitStack
from pathlib import Path

async def migrate_sharded_data(shard_paths: list[Path]) -> int:
    total_records = 0
    
    # Instantiate the dynamic lifecycle stack
    async with AsyncExitStack() as stack:
        # Dynamically acquire an arbitrary number of file handles
        readers = [
            stack.enter_context(path.open("r", encoding="utf-8"))
            for path in shard_paths
        ]
        
        # Register a custom teardown callback for ephemeral state
        scratch_dir = create_temporary_buffer()
        stack.callback(cleanup_scratch_buffer, scratch_dir)
        
        # Dynamically enter an async database connection
        db = await stack.enter_async_context(database_pool.acquire())
        
        # Execute business logic across all dynamically acquired resources
        for reader in readers:
            for line in reader:
                await db.insert(line)
                total_records += 1
                
    # At this boundary, stack guarantees:
    # 1. db released back to pool
    # 2. cleanup_scratch_buffer executed
    # 3. all file handles in readers closed in exact reverse order (LIFO)
    return total_records
