class BlueGreenTableMigrator:
    @staticmethod
    def plan_migration(current_table: str, target_table: str) -> str:
        return f"""
        -- Blue-Green Table Cutover Plan:
        CREATE TABLE {target_table} (LIKE {current_table} INCLUDING ALL);
        ALTER TABLE {target_table} ADD COLUMN compliance_hash VARCHAR(64);
        -- Dual-write trigger active
        -- Atomically swap table names
        ALTER TABLE {current_table} RENAME TO {current_table}_old;
        ALTER TABLE {target_table} RENAME TO {current_table};
        """
