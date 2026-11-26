# Conceptual CPython FunctionType.__get__ implementation:
class Function:
    def __get__(self, instance, owner=None):
        if instance is None:
            # Accessed via the class: AnalyticsWorker.process -> Unbound function
            return self
        # Accessed via an instance: worker.process -> Returns a Bound Method object!
        return MethodType(self, instance)
