# NAIVE, THREAD-UNSAFE IMPLEMENTATION (CATASTROPHIC IN PRODUCTION):
class NaiveLazyProperty:
    def __init__(self, func):
        self.func = func
        self.name = func.__name__

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        val = self.func(instance)
        instance.__dict__[self.name] = val  # Race condition under multi-threading!
        return val
