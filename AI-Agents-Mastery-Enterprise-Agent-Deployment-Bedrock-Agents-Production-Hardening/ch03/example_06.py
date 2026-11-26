import socket
from urllib.parse import urlparse

class PrivateNetworkVerifier:
    """Validates that Azure AI Foundry endpoints resolve to private enterprise IP ranges."""

    @staticmethod
    def verify_private_endpoint(endpoint_url: str) -> Dict[str, Any]:
        hostname = urlparse(endpoint_url).hostname
        if not hostname:
            return {"status": "ERROR", "error": "Invalid URL"}
        
        try:
            ip_address = socket.gethostbyname(hostname)
            octets = [int(x) for x in ip_address.split(".")]
            
            # RFC 1918 Private Ranges: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
            is_private = (
                octets[0] == 10 or
                (octets[0] == 172 and 16 <= octets[1] <= 31) or
                (octets[0] == 192 and octets[1] == 168)
            )
            
            return {
                "hostname": hostname,
                "resolved_ip": ip_address,
                "is_private_vnet": is_private,
                "compliance_status": "APPROVED" if is_private else "REJECTED_PUBLIC_IP"
            }
        except socket.gaierror as e:
            return {"status": "DNS_RESOLUTION_FAILURE", "error": str(e)}

if __name__ == "__main__":
    res = PrivateNetworkVerifier.verify_private_endpoint("https://priv-ai-eastus2.privatelink.api.azureml.ms")
    print("Private Endpoint Verification Result:")
    print(json.dumps(res, indent=2))
