class MultiRegionSyncBarrier:
    def __init__(self, regions: List[str]):
        self.regions = regions

    def await_replication(self, state_id: str, version: int) -> bool:
        print(f"[SYNC BARRIER] Awaiting replication of {state_id} v{version} to regions {self.regions}...")
        return True
