from __future__ import annotations


def extract_root_domain(email: str) -> str:
    host = email.split("@", 1)[1].lower().strip()
    parts = host.split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in {"co.uk", "com.au", "co.in"}:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


if __name__ == "__main__":
    assert extract_root_domain("alex@eu.west.acme.co.uk") == "acme.co.uk"
    assert extract_root_domain("sam@app.globex.com") == "globex.com"
    print("PASS: Multi-part TLD canonicalization verified")
