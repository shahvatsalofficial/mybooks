"""
Architectural Drill 1: Cryptographic License Key Generator with CRC16 Checksum
"""

import os
import binascii
import hmac
import hashlib

SECRET_KEY = b"enterprise-license-master-salt-98f2"

def generate_license_key(user_email: str) -> str:
    # 1. Generate 8 bytes of high-entropy randomness
    rand_bytes = os.urandom(8)
    # 2. Compute 2-byte CRC16 checksum over (email + randomness)
    crc = binascii.crc_hqx(user_email.encode() + rand_bytes, 0xFFFF)
    crc_bytes = crc.to_bytes(2, byteorder="big")
    
    # Combined payload: 10 bytes -> Hex representation (20 chars)
    raw_hex = (rand_bytes + crc_bytes).hex().upper()
    return f"PRO-{raw_hex[:4]}-{raw_hex[4:8]}-{raw_hex[8:12]}-{raw_hex[12:16]}"

def verify_license_checksum(license_key: str, user_email: str) -> bool:
    try:
        parts = license_key.strip().split("-")
        if len(parts) != 5 or parts[0] != "PRO":
            return False
        
        raw_hex = "".join(parts[1:])
        payload = bytes.fromhex(raw_hex)
        rand_bytes = payload[:8]
        expected_crc = int.from_bytes(payload[8:10], byteorder="big")
        
        computed_crc = binascii.crc_hqx(user_email.encode() + rand_bytes, 0xFFFF)
        return hmac.compare_digest(expected_crc.to_bytes(2, "big"), computed_crc.to_bytes(2, "big"))
    except Exception:
        return False

# Verification Test
test_email = "vatsal@suhana-enterprises.com"
key = generate_license_key(test_email)
assert verify_license_checksum(key, test_email) == True
assert verify_license_checksum(key, "attacker@badactor.com") == False
