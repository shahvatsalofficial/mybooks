import ssl

class MutualTLSVerifier:
    @staticmethod
    def create_mtls_ssl_context(ca_cert_path: str, client_cert_path: str, client_key_path: str) -> ssl.SSLContext:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cafile=ca_cert_path)
        context.load_cert_chain(certfile=client_cert_path, keyfile=client_key_path)
        context.verify_mode = ssl.CERT_REQUIRED
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        print("[mTLS SECURITY] Initialized TLS 1.3 context with client certificate validation.")
        return context
