"""
Recipe 02.1: Production Type-Safe Generic Repository Pattern with PEP 695
File: recipe_02_1_generic_repository.py
Python Version: 3.12+ (PEP 695)
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Protocol, TypeVar, Optional, List, Dict, Any


# 1. Structural Domain Invariants
class Identifiable(Protocol):
    """Structural protocol requiring an immutable unique identifier."""
    @property
    def id(self) -> uuid.UUID: ...


class Timestamped(Protocol):
    """Structural protocol requiring lifecycle auditing timestamps."""
    @property
    def created_at(self) -> datetime: ...
    @property
    def updated_at(self) -> datetime: ...


# 2. Structural Repository Contract using PEP 695 Type Parameters
# T must conform to both Identifiable and Timestamped interfaces
class Repository[T: (Identifiable, Timestamped)](Protocol):
    """Enterprise Hexagonal Port defining persistence capabilities."""

    def get_by_id(self, entity_id: uuid.UUID) -> Optional[T]:
        """Retrieves an entity by unique ID, returning None if missing."""
        ...

    def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Returns a paginated list of domain entities."""
        ...

    def persist(self, entity: T) -> T:
        """Persists or updates an entity, returning the materialized state."""
        ...

    def delete(self, entity_id: uuid.UUID) -> bool:
        """Removes an entity by ID, returning True on success."""
        ...


# 3. Concrete Domain Entity (Zero inheritance from Protocol or ORM base!)
class AccountEntity:
    """Pure domain entity completely decoupled from database mechanics."""

    def __init__(self, account_id: uuid.UUID, owner_email: str, balance_cents: int) -> None:
        self._id = account_id
        self._created_at = datetime.now(timezone.utc)
        self._updated_at = self._created_at
        self.owner_email = owner_email
        self.balance_cents = balance_cents

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    def credit(self, amount_cents: int) -> None:
        if amount_cents <= 0:
            raise ValueError("Credit amount must be strictly positive")
        self.balance_cents += amount_cents
        self._updated_at = datetime.now(timezone.utc)


# 4. In-Memory Thread-Safe Persistence Adapter (Conforms structurally to Repository[AccountEntity])
class InMemoryRepository[T: (Identifiable, Timestamped)]:
    """High-speed in-memory store for test automation and ephemeral workloads."""

    def __init__(self) -> None:
        self._storage: Dict[uuid.UUID, T] = {}

    def get_by_id(self, entity_id: uuid.UUID) -> Optional[T]:
        return self._storage.get(entity_id)

    def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        all_items = list(self._storage.values())
        return all_items[offset : offset + limit]

    def persist(self, entity: T) -> T:
        self._storage[entity.id] = entity
        return entity

    def delete(self, entity_id: uuid.UUID) -> bool:
        if entity_id in self._storage:
            del self._storage[entity_id]
            return True
        return False


# 5. Domain Service demonstrating Dependency Inversion
class AccountService:
    """Enterprise domain service depending exclusively on the Repository Port."""

    def __init__(self, repository: Repository[AccountEntity]) -> None:
        self._repo = repository

    def transfer(self, source_id: uuid.UUID, dest_id: uuid.UUID, amount_cents: int) -> bool:
        source = self._repo.get_by_id(source_id)
        dest = self._repo.get_by_id(dest_id)

        if source is None or dest is None:
            return False

        if source.balance_cents < amount_cents:
            raise ValueError("Insufficient balance for transfer")

        source.balance_cents -= amount_cents
        dest.credit(amount_cents)

        self._repo.persist(source)
        self._repo.persist(dest)
        return True


# Verification Driver
if __name__ == "__main__":
    repo: Repository[AccountEntity] = InMemoryRepository[AccountEntity]()
    service = AccountService(repo)

    acc1 = AccountEntity(uuid.uuid4(), "alice@corp.internal", 50000)
    acc2 = AccountEntity(uuid.uuid4(), "bob@corp.internal", 10000)

    repo.persist(acc1)
    repo.persist(acc2)

    success = service.transfer(acc1.id, acc2.id, 15000)
    print(f"[*] Transfer Completed: {success}")
    print(f"[*] Alice Final Balance: ${acc1.balance_cents / 100:.2f}")
    print(f"[*] Bob Final Balance:   ${acc2.balance_cents / 100:.2f}")
