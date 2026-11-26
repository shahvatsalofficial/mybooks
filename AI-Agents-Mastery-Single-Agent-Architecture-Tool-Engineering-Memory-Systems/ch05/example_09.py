@dataclass
class TenantConfig:
    tenant_id: str
    temperature: float
    system_instruction: str
    allowed_tools: List[str]

class MultiTenantAgentFactory:
    def __init__(self):
        self.tenant_store: Dict[str, TenantConfig] = {}

    def register_tenant(self, config: TenantConfig):
        self.tenant_store[config.tenant_id] = config

    def build_agent_runtime(self, tenant_id: str) -> Dict[str, Any]:
        if tenant_id not in self.tenant_store:
            raise KeyError(f"Tenant '{tenant_id}' not found.")
        cfg = self.tenant_store[tenant_id]
        
        # Assemble custom runtime specification
        return {
            "tenant_id": cfg.tenant_id,
            "system_prompt": f"[TENANT: {cfg.tenant_id}] {cfg.system_instruction}",
            "temperature": cfg.temperature,
            "active_tools": cfg.allowed_tools
        }

# Verification
factory = MultiTenantAgentFactory()
factory.register_tenant(TenantConfig(
    tenant_id="acme_corp",
    temperature=0.0,
    system_instruction="Strict financial auditor mode.",
    allowed_tools=["query_db", "export_pdf"]
))
runtime = factory.build_agent_runtime("acme_corp")
print("Synthesized Tenant Runtime:", runtime["system_prompt"])
