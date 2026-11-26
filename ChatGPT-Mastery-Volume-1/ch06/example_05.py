import socket
import ipaddress
from urllib.parse import urlparse

FORBIDDEN_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback
    ipaddress.ip_network("10.0.0.0/8"),       # Private Class A
    ipaddress.ip_network("172.16.0.0/12"),    # Private Class B
    ipaddress.ip_network("192.168.0.0/16"),   # Private Class C
    ipaddress.ip_network("169.254.0.0/16"),   # Cloud Metadata (AWS/GCP/Azure)
]

def validate_webhook_url(target_url: str) -> bool:
    parsed = urlparse(target_url)
    if parsed.scheme != 'https':
        raise ValueError("Webhooks must strictly enforce HTTPS.")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Malformed URL; missing hostname.")

    # Resolve IP address
    try:
        ip_addr_str = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(ip_addr_str)
    except Exception as exc:
        raise ValueError(f"DNS resolution failure for host {hostname}: {str(exc)}")

    for forbidden_net in FORBIDDEN_NETWORKS:
        if ip_obj in forbidden_net:
            raise ValueError(f"SSRF Hazard: Destination IP {ip_obj} resolves to a private or link-local address.")

    return True

# Verification
assert validate_webhook_url("https://hooks.slack.com/services/T00/B00/X00") == True
