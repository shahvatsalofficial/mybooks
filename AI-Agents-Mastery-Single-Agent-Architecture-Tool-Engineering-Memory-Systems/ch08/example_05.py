class TenantAPIKeyGovernor:
    def __init__(self):
        # Maps SHA-256(key) -> {tenant_id, tier, max_rpm}
        self.key_directory: Dict[str, Dict[str, Any]] = {}
        self.request_windows: Dict[str, deque] = {}

    def register_key(self, raw_api_key: str, tenant_id: str, tier: str = "enterprise", max_rpm: int = 120):
        key_hash = hashlib.sha256(raw_api_key.encode("utf-8")).hexdigest()
        self.key_directory[key_hash] = {"tenant_id": tenant_id, "tier": tier, "max_rpm": max_rpm}

    def authenticate_and_throttle(self, raw_api_key: str) -> str:
        key_hash = hashlib.sha256(raw_api_key.encode("utf-8")).hexdigest()
        if key_hash not in self.key_directory:
            raise PermissionError("HTTP 401 Unauthorized: Invalid or revoked API key.")

        tenant_info = self.key_directory[key_hash]
        tenant_id = tenant_info["tenant_id"]
        max_rpm = tenant_info["max_rpm"]

        # Sliding window check
        now = time.time()
        if tenant_id not in self.request_windows:
            self.request_windows[tenant_id] = deque()
            
        window = self.request_windows[tenant_id]
        # Evict timestamps older than 60 seconds
        while window and (now - window[0]) > 60.0:
            window.popleft()

        if len(window) >= max_rpm:
            raise PermissionError(f"HTTP 429 Too Many Requests: Tenant {tenant_id} exceeded {max_rpm} RPM limit.")

        window.append(now)
        return tenant_id

# Verification
key_gov = TenantAPIKeyGovernor()
key_gov.register_key("sk_live_acme_8812904", "tenant_acme", max_rpm=2)
tid = key_gov.authenticate_and_throttle("sk_live_acme_8812904")
print(f"Authenticated Tenant: {tid}")
