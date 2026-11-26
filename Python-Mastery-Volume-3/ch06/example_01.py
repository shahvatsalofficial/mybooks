# Establishing a Zero-Trust mTLS client in httpx
import ssl
import httpx

def create_mtls_client(cert_file: str, key_file: str, ca_bundle: str) -> httpx.AsyncClient:
    """Configures non-blocking HTTP client with mutual cryptographic identity."""
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=ca_bundle)
    # Load client's cryptographic identity certificate and private key
    ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.check_hostname = True
    
    return httpx.AsyncClient(verify=ssl_context, timeout=5.0)
