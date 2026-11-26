# Declarative test matrix with custom readable IDs
@pytest.mark.parametrize(
    ("raw_input", "expected_status", "expected_error_code"),
    [
        ({"amount": "100.00", "currency": "USD"}, 201, None),
        ({"amount": "-50.00", "currency": "USD"}, 422, "INVALID_AMOUNT"),
        ({"amount": "100.00", "currency": "INVALID"}, 422, "UNSUPPORTED_CURRENCY"),
        ({}, 422, "MISSING_REQUIRED_FIELDS"),
    ],
    ids=["valid_transaction", "negative_amount", "unsupported_currency", "empty_payload"],
)
async def test_transaction_validation_matrix(
    async_client: httpx.AsyncClient,
    raw_input: dict,
    expected_status: int,
    expected_error_code: str | None,
) -> None:
    response = await async_client.post("/api/v1/transactions", json=raw_input)
    assert response.status_code == expected_status
    if expected_error_code:
        assert response.json()["error_code"] == expected_error_code
