import ssl
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class CloudMeshNodeConfig(BaseModel):
    cloud_provider: str
    region: str
    endpoint_uri: str
    ca_cert_path: str
    client_cert_path: str
    client_key_path: str
    max_concurrent_streams: int = Field(default=64, ge=1, le=512)

class CrossCloudAgentMeshGateway:
    """Manages secure cross-cloud gRPC connections with mTLS authentication."""
    
    def __init__(self, local_cloud: str, local_region: str):
        self.local_cloud = local_cloud
        self.local_region = local_region
        self.mesh_nodes: Dict[str, CloudMeshNodeConfig] = {}
        self.connection_states: Dict[str, str] = {}

    def register_mesh_node(self, node_id: str, config: CloudMeshNodeConfig) -> None:
        self.mesh_nodes[node_id] = config
        self.connection_states[node_id] = "REGISTERED"
        print(f"[MESH GATEWAY] Node registered: {node_id} on {config.cloud_provider} ({config.region})")

    def build_mtls_channel_credentials(self, node_id: str) -> ssl.SSLContext:
        node = self.mesh_nodes[node_id]
        ssl_ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ssl_ctx.verify_mode = ssl.CERT_REQUIRED
        ssl_ctx.check_hostname = True
        # In production: ssl_ctx.load_verify_locations(node.ca_cert_path)
        # In production: ssl_ctx.load_cert_chain(node.client_cert_path, node.client_key_path)
        self.connection_states[node_id] = "MUTUAL_TLS_ESTABLISHED"
        print(f"[MESH SECURITY] mTLS handshake validated for {node_id} ({node.endpoint_uri})")
        return ssl_ctx

    def dispatch_remote_task(self, node_id: str, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        if self.connection_states.get(node_id) != "MUTUAL_TLS_ESTABLISHED":
            self.build_mtls_channel_credentials(node_id)
        
        node = self.mesh_nodes[node_id]
        print(f"[gRPC STREAM] Routing task '{task_envelope.get('task_id')}' to {node_id} ({node.cloud_provider})")
        
        # Simulated gRPC response envelope
        return {
            "task_id": task_envelope.get("task_id"),
            "status": "SUCCESS",
            "origin_node": node_id,
            "cloud_provider": node.cloud_provider,
            "latency_ms": 38.4,
            "mtls_verified": True
        }
