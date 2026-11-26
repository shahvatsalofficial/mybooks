def retrieve_public_profile(user_id: str) -> dict:
    try:
        return internal_ldap_lookup(user_id)
    except InternalLDAPCommunicationError:
        # Suppress internal infrastructure tracebacks from client output
        raise UserNotFoundError(f"User {user_id} does not exist.") from None
