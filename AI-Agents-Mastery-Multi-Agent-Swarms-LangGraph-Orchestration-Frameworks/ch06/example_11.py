class SchemaVersionNegotiator:
    SUPPORTED_VERSIONS = ["A2A/1.0", "A2A/1.1"]

    @classmethod
    def negotiate_version(cls, client_version: str) -> str:
        if client_version in cls.SUPPORTED_VERSIONS:
            return client_version
        raise ValueError(f"Incompatible protocol version '{client_version}'. Server supports {cls.SUPPORTED_VERSIONS}")
