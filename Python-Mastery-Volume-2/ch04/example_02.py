"""
Recipe 04.1: Out-of-Line ABI Mode CFFI Shared Library Wrapper
Architecture: High-performance CFFI bridge wrapping POSIX / OpenSSL shared libraries.
Target Runtime: Python 3.12+ (CPython)
"""

from __future__ import annotations
import os
import sys
from cffi import FFI

ffi = FFI()

# Declare C signatures for cryptographic SHA-256 primitives (OpenSSL libcrypto)
ffi.cdef("""
    typedef struct env_md_ctx_st EVP_MD_CTX;
    typedef struct env_md_st EVP_MD;

    EVP_MD_CTX *EVP_MD_CTX_new(void);
    void EVP_MD_CTX_free(EVP_MD_CTX *ctx);
    const EVP_MD *EVP_sha256(void);
    int EVP_DigestInit_ex(EVP_MD_CTX *ctx, const EVP_MD *type, void *impl);
    int EVP_DigestUpdate(EVP_MD_CTX *ctx, const void *d, size_t cnt);
    int EVP_DigestFinal_ex(EVP_MD_CTX *ctx, unsigned char *md, unsigned int *s);
""")

# Resolve platform-specific shared library
if sys.platform.startswith("linux"):
    libcrypto_path = "libcrypto.so.3"
elif sys.platform == "darwin":
    libcrypto_path = "libcrypto.dylib"
else:
    libcrypto_path = "libcrypto-3-x64.dll"

try:
    crypto = ffi.dlopen(libcrypto_path)
except OSError:
    # Fallback to standard libcrypto SONAME
    crypto = ffi.dlopen("libcrypto.so")


class NativeSHA256Accelerator:
    """High-throughput CFFI wrapper providing sub-microsecond SHA-256 digests."""

    def __init__(self) -> None:
        self._ctx = crypto.EVP_MD_CTX_new()
        if self._ctx == ffi.NULL:
            raise MemoryError("Failed to allocate OpenSSL EVP_MD_CTX structure")
        self._md = crypto.EVP_sha256()

    def __del__(self) -> None:
        """Deterministic cleanup of OpenSSL C context."""
        if hasattr(self, "_ctx") and self._ctx != ffi.NULL:
            crypto.EVP_MD_CTX_free(self._ctx)
            self._ctx = ffi.NULL

    def compute_digest(self, data: bytes) -> bytes:
        """Computes SHA-256 digest using direct C pointers without Python memory copying."""
        if crypto.EVP_DigestInit_ex(self._ctx, self._md, ffi.NULL) != 1:
            raise RuntimeError("EVP_DigestInit_ex failed")

        # Pass direct pointer to Python bytes internal memory buffer
        data_ptr = ffi.from_buffer("const char[]", data)
        if crypto.EVP_DigestUpdate(self._ctx, data_ptr, len(data)) != 1:
            raise RuntimeError("EVP_DigestUpdate failed")

        output_buffer = ffi.new("unsigned char[32]")
        output_len = ffi.new("unsigned int *")

        if crypto.EVP_DigestFinal_ex(self._ctx, output_buffer, output_len) != 1:
            raise RuntimeError("EVP_DigestFinal_ex failed")

        return bytes(ffi.buffer(output_buffer, output_len[0]))


# Demonstration & Verification
if __name__ == "__main__":
    import hashlib

    accelerator = NativeSHA256Accelerator()
    payload = b"High-throughput native bridge transaction payload for CFFI demonstration."

    native_hash = accelerator.compute_digest(payload)
    stdlib_hash = hashlib.sha256(payload).digest()

    print(f"Native CFFI Hash: {native_hash.hex()}")
    print(f"Stdlib Hash:      {stdlib_hash.hex()}")
    assert native_hash == stdlib_hash, "Hash verification failure!"
    print("Verification Successful: CFFI SHA-256 matches hashlib standard.")
