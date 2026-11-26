from typing import Concatenate

# Decorator that removes 'RequestContext' from the external API signature
def inject_context(func: Callable[Concatenate[RequestContext, P], R]) -> Callable[P, R]:
    ...
