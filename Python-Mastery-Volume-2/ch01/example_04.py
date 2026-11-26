"""
Dynamic Metaclass Conflict Resolver
Computes the most derived common metaclass across all base classes.
"""

from typing import Any, Tuple, Type


def resolve_metaclass_conflicts(
    bases: Tuple[Type[Any], ...],
    explicit_meta: Type[Any] | None = None,
) -> Type[Any]:
    """Dynamically resolves or synthesizes a unified metaclass for a set of bases.
    
    Args:
        bases: Tuple of parent classes to be inherited.
        explicit_meta: Metaclass explicitly specified in the class header, if any.
        
    Returns:
        The most derived metaclass that satisfies all inheritance constraints.
    """
    metaclasses = set()
    if explicit_meta:
        metaclasses.add(explicit_meta)
    for base in bases:
        metaclasses.add(type(base))

    # Strip redundant base metaclasses that are already subclasses of others in the set
    candidates = list(metaclasses)
    needed = set(candidates)
    for m1 in candidates:
        for m2 in candidates:
            if m1 is not m2 and issubclass(m1, m2):
                needed.discard(m2)

    if len(needed) == 1:
        return needed.pop()

    # Multiple distinct metaclass branches exist: dynamically generate a synthesized child metaclass
    composite_name = "_".join(m.__name__ for m in sorted(needed, key=lambda x: x.__name__))
    composite_meta = type(f"CompositeMeta_{composite_name}", tuple(needed), {})
    return composite_meta
