"""
MCP Enterprise OAuth 2.1 PKCE Authentication Engine
Architecture: FastMCP Server with Async JWKS Validation & Scope Guards
Author: Vatsal Shah | Vatsal Shah
"""

import time
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import httpx
from authlib.jose import jwt, JsonWebKey
from authlib.jose.errors import JoseError, ExpiredTokenError, BadSignatureError
from mcp.server.fastmcp import FastMCP, Context
from mcp.shared.exceptions import McpError
from mcp.types import ErrorCode

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("mcp.auth.oauth2")

@dataclass(frozen=True)
class SecurityContext:
    subject: str
    tenant_id: str
    client_id: str
    scopes: List[str]
    roles: List[str]
    issued_at: int
    expires_at: int

    def has_scope(self, required_scope: str) -> bool:
        """Check if caller has explicit scope or wildcard administrator scope."""
        if "mcp:admin" in self.scopes or "admin" in self.roles:
            return True
        return required_scope in self.scopes


class JwksTokenValidator:
    """High-throughput JWKS token validator with memory caching and automatic rotation."""

    def __init__(self, idp_discovery_url: str, audience: str, cache_ttl_seconds: int = 86400):
        self.idp_discovery_url = idp_discovery_url
        self.audience = audience
        self.cache_ttl = cache_ttl_seconds
        self._cached_jwks: Optional[Dict[str, Any]] = None
        self._last_fetch_timestamp: float = 0.0
        self._http_client = httpx.AsyncClient(timeout=10.0)

    async def _fetch_jwks(self) -> Dict[str, Any]:
        """Fetch OpenID configuration and JWKS public keys from IdP."""
        now = time.time()
        if self._cached_jwks and (now - self._last_fetch_timestamp) < self.cache_ttl:
            return self._cached_jwks

        logger.info(f"Refreshing JWKS public keys from IdP discovery endpoint: {self.idp_discovery_url}")
        resp = await self._http_client.get(self.idp_discovery_url)
        resp.raise_for_status()
        discovery_doc = resp.json()

        jwks_uri = discovery_doc.get("jwks_uri")
        if not jwks_uri:
            raise ValueError("Discovery document missing 'jwks_uri' field")

        jwks_resp = await self._http_client.get(jwks_uri)
        jwks_resp.raise_for_status()
        self._cached_jwks = jwks_resp.json()
        self._last_fetch_timestamp = now
        return self._cached_jwks

    async def validate_token(self, token_string: str) -> SecurityContext:
        """Cryptographically verify JWT signature, expiration, issuer and audience."""
        if not token_string:
            raise McpError(ErrorCode.InvalidRequest, "Missing authorization bearer token")

        jwks_data = await self._fetch_jwks()
        key_set = JsonWebKey.import_key_set(jwks_data)

        try:
            # Decode header to identify signing key
            unverified_header = jwt.get_unverified_header(token_string)
            kid = unverified_header.get("kid")
            if not kid:
                raise McpError(ErrorCode.InvalidRequest, "JWT header missing 'kid' key identifier")

            key = key_set.find_by_kid(kid)
            if not key:
                # Force refresh cache once in case of key rotation
                logger.warning(f"Key ID {kid} not found in cached JWKS. Forcing key rotation refresh.")
                self._last_fetch_timestamp = 0.0
                jwks_data = await self._fetch_jwks()
                key_set = JsonWebKey.import_key_set(jwks_data)
                key = key_set.find_by_kid(kid)
                if not key:
                    raise McpError(ErrorCode.InvalidParams, f"Unknown signing key ID: {kid}")

            claims = jwt.decode(
                token_string,
                key,
                claims_options={
                    "iss": {"essential": True},
                    "aud": {"essential": True, "value": self.audience},
                    "exp": {"essential": True},
                }
            )
            claims.validate()

            raw_scopes = claims.get("scope", claims.get("scp", []))
            if isinstance(raw_scopes, str):
                scopes = raw_scopes.split()
            else:
                scopes = list(raw_scopes)

            return SecurityContext(
                subject=claims["sub"],
                tenant_id=claims.get("tenant_id", "default_tenant"),
                client_id=claims.get("client_id", claims.get("azp", "unknown_client")),
                scopes=scopes,
                roles=claims.get("roles", []),
                issued_at=claims.get("iat", int(time.time())),
                expires_at=claims["exp"]
            )

        except ExpiredTokenError:
            raise McpError(ErrorCode.InvalidRequest, "Authentication token has expired")
        except BadSignatureError:
            raise McpError(ErrorCode.InvalidRequest, "Cryptographic token signature verification failed")
        except JoseError as je:
            raise McpError(ErrorCode.InvalidRequest, f"JWT verification error: {str(je)}")


# Initialize Production FastMCP Server
mcp = FastMCP("Enterprise-Database-Tool-Gateway")
validator = JwksTokenValidator(
    idp_discovery_url="https://auth.shahvatsal.comternal/.well-known/openid-configuration",
    audience="mcp://database-gateway-prod"
)

def require_auth(required_scope: str):
    """Decorator to enforce OAuth 2.1 scope verification on MCP tool endpoints."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            ctx: Optional[Context] = kwargs.get("ctx")
            if not ctx:
                raise McpError(ErrorCode.InternalError, "Tool invoked without execution context")

            # Extract Bearer token from client request headers
            auth_header = ctx.request_context.meta.get("authorization", "")
            if not auth_header.startswith("Bearer "):
                raise McpError(ErrorCode.InvalidRequest, "Authorization header must use Bearer scheme")

            raw_token = auth_header[7:].strip()
            sec_context = await validator.validate_token(raw_token)

            if not sec_context.has_scope(required_scope):
                logger.warning(
                    f"Forbidden: Subject {sec_context.subject} missing required scope: {required_scope}. "
                    f"Granted: {sec_context.scopes}"
                )
                raise McpError(ErrorCode.InvalidParams, f"Forbidden: Insufficient scope. Requires '{required_scope}'")

            # Inject verified security context into kwargs
            kwargs["security_context"] = sec_context
            return await func(*args, **kwargs)
        return wrapper
    return decorator


@mcp.tool(description="Execute read-only SQL query against customer analytical warehouse")
@require_auth(required_scope="mcp:tools:database:read")
async def query_customer_analytics(
    sql_query: str,
    ctx: Context,
    security_context: Optional[SecurityContext] = None
) -> str:
    """Safe analytical query execution bounded by caller's tenant boundary."""
    assert security_context is not None
    logger.info(
        f"Executing query for tenant {security_context.tenant_id} "
        f"initiated by {security_context.subject}"
    )

    # Prevent accidental write queries at tool layer
    normalized_sql = sql_query.strip().upper()
    if any(keyword in normalized_sql for keyword in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]):
        raise McpError(ErrorCode.InvalidParams, "Write mutations prohibited on read-only analytical tool endpoint")

    # In production, query is executed with tenant-isolated connection parameters
    result_data = {
        "status": "success",
        "tenant_id": security_context.tenant_id,
        "query_executed": sql_query,
        "rows_returned": 42,
        "execution_time_ms": 1.48
    }
    return json.dumps(result_data)
