# Python 3.12+ Scoped Type Alias
type JSONPrimitive = str | int | float | bool | None
type JSONValue = JSONPrimitive | list[JSONValue] | dict[str, JSONValue]
type Matrix[T: (int, float)] = list[list[T]]
