from __future__ import annotations

import hashlib
import hmac
import json
import time
from enum import IntEnum
from typing import Dict, List, Set
from pydantic import BaseModel, Field


class ClearanceLevel(IntEnum):
    PUBLIC = 0
    INTERNAL = 1
    CONFIDENTIAL = 2
    RESTRICTED = 3


class PrincipalContext(BaseModel):
    user_id: str
    tenant_id: str
    roles: Set[str] = Field(default_factory=set)
    department: str
    clearance: ClearanceLevel = ClearanceLevel.INTERNAL
    exp_epoch: int


class DocumentAcl(BaseModel):
    doc_id: str
    tenant_id: str
    allowed_roles: Set[str] = Field(default_factory=set)
    allowed_users: Set[str] = Field(default_factory=set)
    min_clearance: ClearanceLevel = ClearanceLevel.INTERNAL
    is_revoked: bool = False


class ClaimVerifier:
    """Verifies HMAC-signed identity payloads and expands role hierarchies."""

    ROLE_HIERARCHY: Dict[str, Set[str]] = {
        "vp_engineering": {"eng_lead", "engineer", "employee"},
        "eng_lead": {"engineer", "employee"},
        "sec_auditor": {"compliance_viewer", "employee"},
        "contractor": {"external_support"},
    }

    def __init__(self, signing_secret: str) -> None:
        self._secret = signing_secret.encode("utf-8")

    def sign_claims(self, payload: Dict) -> str:
        raw = json.dumps(payload, sort_keys=True).encode("utf-8")
        sig = hmac.new(self._secret, raw, hashlib.sha256).hexdigest()
        return f"{raw.decode('utf-8')}|{sig}"

    def verify_and_build(self, token: str, now_epoch: int | None = None) -> PrincipalContext:
        raw_str, provided_sig = token.rsplit("|", 1)
        expected_sig = hmac.new(self._secret, raw_str.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, provided_sig):
            raise PermissionError("Invalid identity token signature.")

        data = json.loads(raw_str)
        current = now_epoch if now_epoch is not None else int(time.time())
        if int(data["exp_epoch"]) < current:
            raise PermissionError("Identity token expired.")

        expanded_roles: Set[str] = set(data.get("roles", []))
        for r in list(expanded_roles):
            expanded_roles.update(self.ROLE_HIERARCHY.get(r, set()))

        return PrincipalContext(
            user_id=data["user_id"],
            tenant_id=data["tenant_id"],
            roles=expanded_roles,
            department=data["department"],
            clearance=ClearanceLevel(int(data.get("clearance", 1))),
            exp_epoch=int(data["exp_epoch"]),
        )


def demo_claim_verifier() -> None:
    verifier = ClaimVerifier("prod-secret-key-2026")
    tok = verifier.sign_claims({
        "user_id": "u_8841",
        "tenant_id": "acme_corp",
        "roles": ["eng_lead"],
        "department": "platform",
        "clearance": 2,
        "exp_epoch": int(time.time()) + 600,
    })
    principal = verifier.verify_and_build(tok)
    print(f"Verified: {principal.user_id} | Clearance: {principal.clearance.name} | Roles: {sorted(principal.roles)}")


if __name__ == "__main__":
    demo_claim_verifier()
