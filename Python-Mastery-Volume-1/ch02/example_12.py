# Legacy Pre-3.11 Workaround
T = TypeVar('T', bound='BaseQueryBuilder')

class BaseQueryBuilder:
    def filter(self: T, condition: str) -> T:
        # Complex TypeVar boilerplate required to return derived type
        return self
