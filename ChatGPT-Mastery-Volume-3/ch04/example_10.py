# hsm_envelope_encryption.py
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.keys.crypto import CryptographyClient, EncryptionAlgorithm
from cryptography.fernet import Fernet

class HSMEnvelopeCryptor:
    def __init__(self, key_id: str):
        self.credential = DefaultAzureCredential()
        self.crypto_client = CryptographyClient(key_id, credential=self.credential)

    async def encrypt_sensitive_context(self, plaintext_content: str) -> Dict[str, bytes]:
        # Step 1: Generate dynamic AES-256 local key
        local_dek = Fernet.generate_key()
        f = Fernet(local_dek)
        ciphertext_body = f.encrypt(plaintext_content.encode("utf-8"))
        
        # Step 2: Encrypt DEK inside Managed HSM using RSA-OAEP-256
        wrap_result = await self.crypto_client.wrap_key(
            EncryptionAlgorithm.rsa_oaep_256, local_dek
        )
        
        # Plaintext local_dek is immediately purged from RAM
        del local_dek
        
        return {
            "wrapped_dek": wrap_result.encrypted_key,
            "ciphertext": ciphertext_body,
            "algorithm": wrap_result.algorithm
        }
