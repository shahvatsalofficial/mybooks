class ProtocolHandler:
    def __init_subclass__(cls, protocol_id: str, max_payload: int = 65536, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)  # Cooperative super() dispatch
        cls._protocol_id = protocol_id
        cls._max_payload = max_payload
        # Validate that required interface methods are implemented
        if not hasattr(cls, "serialize") or not callable(getattr(cls, "serialize")):
            raise TypeError(f"Class '{cls.__name__}' must implement callable 'serialize(self)' method.")
