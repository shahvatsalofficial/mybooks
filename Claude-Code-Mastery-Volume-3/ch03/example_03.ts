// SECURITY INVARIANT: All financial transactions must acquire a distributed Redis lock
// before modifying account balances. Never execute direct database updates without lock.
