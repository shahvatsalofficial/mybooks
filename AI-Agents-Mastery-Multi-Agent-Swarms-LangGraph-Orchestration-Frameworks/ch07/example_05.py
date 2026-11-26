class MockRedisDistributedLock:
    def __init__(self, resource_name: str, lock_ttl_sec: float = 5.0):
        self.resource_name = f"lock:{resource_name}"
        self.lock_ttl_sec = lock_ttl_sec
        self.lock_token = str(uuid.uuid4())
        self.acquired = False

    def __enter__(self):
        print(f"[REDIS LOCK] Attempting lock acquisition on '{self.resource_name}' (TTL: {self.lock_ttl_sec}s)...")
        # In production: redis_client.set(self.resource_name, self.lock_token, nx=True, ex=self.lock_ttl_sec)
        self.acquired = True
        print(f"[REDIS LOCK] ACQUIRED! Token: {self.lock_token}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.acquired:
            print(f"[REDIS LOCK] Releasing lock on '{self.resource_name}' with token {self.lock_token}...")
            # In production: Execute Lua script verifying token before deletion
            self.acquired = False
