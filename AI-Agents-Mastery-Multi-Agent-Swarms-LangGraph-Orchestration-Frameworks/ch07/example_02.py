class ConcurrentSharedStore:
    def __init__(self):
        self._store: Dict[str, VersionedState] = {}

    def get(self, state_id: str) -> Optional[VersionedState]:
        record = self._store.get(state_id)
        if not record:
            return None
        # Return deep copy to prevent in-place mutation
        return record.model_copy(deep=True)

    def write_initial(self, state_id: str, data: Dict[str, Any], agent_name: str) -> VersionedState:
        record = VersionedState(
            state_id=state_id,
            version=1,
            data=data,
            last_updated_by=agent_name
        )
        self._store[state_id] = record
        return record

    def update_atomic(self, state_id: str, expected_version: int, new_data: Dict[str, Any], agent_name: str) -> VersionedState:
        current = self._store.get(state_id)
        if not current:
            raise KeyError(f"State ID '{state_id}' does not exist.")

        # Optimistic Concurrency Verification
        if current.version != expected_version:
            raise StateConflictError(
                f"OCC Conflict on '{state_id}'! Agent '{agent_name}' attempted update with stale version {expected_version}, "
                f"but current state is version {current.version} (updated by '{current.last_updated_by}')."
            )

        # Atomic Commit: Update data and increment version
        updated_record = VersionedState(
            state_id=state_id,
            version=current.version + 1,
            data=new_data,
            last_updated_by=agent_name,
            last_updated_at=time.time()
        )
        self._store[state_id] = updated_record
        return updated_record
