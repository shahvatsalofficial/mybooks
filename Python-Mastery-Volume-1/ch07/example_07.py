import weakref

class AuthTokenHardened:
    def __init__(self, token_str: str, session: ClientSession) -> None:
        self.token_str = token_str
        # Weak reference: Zero increment to ob_refcnt! Eliminates cycle!
        self._session_ref = weakref.ref(session)

    @property
    def session(self) -> ClientSession | None:
        return self._session_ref()
