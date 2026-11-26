# DISASTROUS TESTING ANTI-PATTERN
@pytest.fixture
def sqlite_engine():
    # Attempting to test PostgreSQL models against SQLite!
    return create_engine("sqlite:///:memory:")
