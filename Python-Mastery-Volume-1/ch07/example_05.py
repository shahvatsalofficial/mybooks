# DEFECTIVE PRODUCTION CODE (Pre-Incident)
class ClientSession:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.auth_token: AuthToken | None = None

    def __del__(self) -> None:
        # Custom finalizer attempting to log termination
        logger.info(f"Cleaning up session {self.session_id}")


class AuthToken:
    def __init__(self, token_str: str, session: ClientSession) -> None:
        self.token_str = token_str
        self.session = session # Circular reference back to ClientSession!
