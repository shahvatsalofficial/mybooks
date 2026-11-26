# Encapsulation pattern for collections inside aggregate roots
@property
def line_items(self) -> Sequence[OrderLine]:
    return tuple(self._line_items)
