from typing import Self

class ResilientClientBuilder:
    def __init__(self) -> None:
        self._timeout_ms: int = 5000
        self._retries: int = 3
        self._endpoint: str = ""

    def with_timeout(self, timeout_ms: int) -> Self:
        self._timeout_ms = timeout_ms
        return self

    def with_retries(self, retries: int) -> Self:
        self._retries = retries
        return self

    def with_endpoint(self, endpoint: str) -> Self:
        self._endpoint = endpoint
        return self

class SecureTLSClientBuilder(ResilientClientBuilder):
    def with_mutual_tls(self, cert_path: str) -> Self:
        self._cert_path = cert_path
        return self

# Perfect type inference throughout the entire chain:
client = (
    SecureTLSClientBuilder()
    .with_timeout(1000)      # Returns SecureTLSClientBuilder!
    .with_retries(5)          # Returns SecureTLSClientBuilder!
    .with_mutual_tls("/pki") # Validated on the derived builder!
)
