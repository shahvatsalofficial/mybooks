class StateSchemaMigrationGateway:
    CURRENT_SCHEMA_VERSION = 2

    @classmethod
    def migrate_checkpoint_payload(cls, raw_state: Dict[str, Any]) -> Dict[str, Any]:
        state_version = raw_state.get("_schema_version", 1)
        upgraded_state = raw_state.copy()
        
        # Migration from v1 to v2: Add mandatory security and compliance defaults
        if state_version == 1:
            print(f"[MIGRATION] Upgrading state checkpoint from v1 to v2...")
            upgraded_state["_schema_version"] = 2
            upgraded_state["compliance_status"] = "PENDING_AUDIT"
            upgraded_state["trace_tags"] = []
            
        return upgraded_state
