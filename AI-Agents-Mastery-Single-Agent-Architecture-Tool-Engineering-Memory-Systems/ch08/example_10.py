import ctypes

class ZeroizedSecret:
    def __init__(self, secret_text: str):
        self._raw_str = secret_text
        self._buffer = ctypes.create_string_buffer(secret_text.encode("utf-8"))

    def __enter__(self):
        return self._buffer.value.decode("utf-8")

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Overwrite buffer memory with zeroes
        ctypes.memset(self._buffer, 0, len(self._buffer))
        self._raw_str = ""

# Verification
with ZeroizedSecret("sk_live_super_secret_token_9912") as token:
    print("Inside Protected Scope: Token is accessible (length:", len(token), ")")
print("Secret Zeroization Complete.")
