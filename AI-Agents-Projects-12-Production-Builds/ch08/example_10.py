from __future__ import annotations

import re
from typing import Dict
from pydantic import BaseModel, Field


class TokenVault(BaseModel):
    forward_map: Dict[str, str] = Field(default_factory=dict)
    reverse_map: Dict[str, str] = Field(default_factory=dict)


class ReversiblePseudonymizer:
    """Replaces emails with indexed tokens and optionally re-hydrates for privileged roles."""

    EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

    def pseudonymize(self, text: str, vault: TokenVault) -> str:
        counter = len(vault.forward_map)

        def _repl(match: re.Match[str]) -> str:
            nonlocal counter
            raw = match.group(0)
            if raw not in vault.forward_map:
                counter += 1
                tok = f"[EMAIL_{counter}]"
                vault.forward_map[raw] = tok
                vault.reverse_map[tok] = raw
            return vault.forward_map[raw]

        return self.EMAIL_RE.sub(_repl, text)

    def rehydrate(self, text: str, vault: TokenVault, allow_pii_view: bool) -> str:
        if not allow_pii_view:
            return text
        out = text
        for tok, raw in vault.reverse_map.items():
            out = out.replace(tok, raw)
        return out


def demo_pseudonymizer() -> None:
    vault = TokenVault()
    pseudo = ReversiblePseudonymizer()
    masked = pseudo.pseudonymize("Compare alice@acme.com and bob@acme.com.", vault)
    print(f"To LLM: {masked}")
    print(f"To Contractor: {pseudo.rehydrate('Owner is [EMAIL_1].', vault, allow_pii_view=False)}")
    print(f"To Auditor: {pseudo.rehydrate('Owner is [EMAIL_1].', vault, allow_pii_view=True)}")


if __name__ == "__main__":
    demo_pseudonymizer()
