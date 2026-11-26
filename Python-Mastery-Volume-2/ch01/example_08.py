# CATASTROPHIC FLAW IN v4.12.0 PRODUCTION CODE:
class DynamicPayloadMeta(type):
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        # Binds closure over 'cls', preventing deallocation:
        cls.validate = lambda self: self._validate_schema(cls)
