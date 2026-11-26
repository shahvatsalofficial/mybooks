# PRODUCTION HOTFIX: Double-Checked Thread-Safe Cache Descriptor
class VolatilitySurfaceDescriptor:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cache_name = "_surface_cache"

    def __get__(self, instance: InstrumentContract, owner: type | None = None) -> Matrix:
        if instance is None:
            return self

        # 1. Fast path: atomic read
        val = getattr(instance, self._cache_name, None)
        if val is not None:
            return val

        # 2. Mutex-guarded slow path: stampede suppression
        with self._lock:
            val = getattr(instance, self._cache_name, None)
            if val is not None:
                return val

            # Execute single analytical load
            computed = db_client.load_surface(instance.ticker)
            setattr(instance, self._cache_name, computed)
            return computed
