# security/dependencies.py
"""FastAPI route dependencies enforcing fine-grained Zero-Trust scopes and RBAC."""

from __future__ import annotations
from collections.abc import Callable, Sequence
import logging

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from security.jwt_validator import AsymmetricJWTValidator, TokenClaims

logger = logging.getLogger("auth_dependencies")

# Bearer token extractor
security_scheme = HTTPBearer(auto_error=True)

# Central validator instance (configured via environment variables in production)
validator = AsymmetricJWTValidator(
    jwks_url="https://auth.enterprise.internal/.well-known/jwks.json",
    expected_issuer="https://auth.enterprise.internal",
    expected_audience="https://api.enterprise.internal",
)


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
) -> TokenClaims:
    """Extracts and validates cryptographic bearer token from Authorization header."""
    try:
        claims = await validator.validate_token(credentials.credentials)
        return claims
    except PermissionError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(err),
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""},
        )


class RequireScopes:
    """Factory creating route dependencies enforcing mandatory OAuth 2.0 scopes."""

    def __init__(self, required_scopes: Sequence[str]) -> None:
        self.required_scopes = set(required_scopes)

    def __call__(self, claims: TokenClaims = Depends(get_current_principal)) -> TokenClaims:
        granted_scopes = set(claims.scopes)
        missing_scopes = self.required_scopes - granted_scopes

        if missing_scopes:
            logger.warning(
                "Principal %s DENIED access. Missing required scopes: %s",
                claims.sub,
                missing_scopes,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "insufficient_scope",
                    "message": "User does not possess authorized scopes for this operation.",
                    "missing_scopes": list(missing_scopes),
                },
            )
        return claims


class RequireTenantIsolation:
    """Guarantees that a user can access records solely within their own tenant organization."""

    def __init__(self, tenant_id_param_name: str = "tenant_id") -> None:
        self.param_name = tenant_id_param_name

    def __call__(
        self,
        tenant_id: str,
        claims: TokenClaims = Depends(get_current_principal),
    ) -> TokenClaims:
        if claims.tenant_id != tenant_id and "GLOBAL_SUPERADMIN" not in claims.roles:
            logger.critical(
                "Cross-tenant access violation attempt! User %s (Tenant %s) attempted to access Tenant %s",
                claims.sub,
                claims.tenant_id,
                tenant_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cross-tenant resource manipulation prohibited.",
            )
        return claims
