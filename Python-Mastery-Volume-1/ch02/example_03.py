from typing import TypeVar, Generic

T = TypeVar('T')                          # Invariant
T_co = TypeVar('T_co', covariant=True)     # Covariant
T_contra = TypeVar('T_contra', contravariant=True) # Contravariant

class ReadOnlyStream(Generic[T_co]):
    def read_next(self) -> T_co: ...
