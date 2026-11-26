# VULNERABLE HISTORICAL CODE (PRE-INCIDENT)
# In every microservice:
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-production-key-2024")

def authenticate_request(token: str):
    # CRITICAL SECURITY VULNERABILITY:
    # Uses symmetric HS256. Anyone possessing 'JWT_SECRET' can SIGN tokens!
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
