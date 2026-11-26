# Python 3.12+ Native Syntax - Zero manual variance boilerplate!
class ReadOnlyStream[T]:
    def read_next(self) -> T: ...
    # Compiler automatically proves T is covariant!
