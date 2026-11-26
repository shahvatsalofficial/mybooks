# Testing HTTP clients via transport-level mocking with respx
import httpx
import pytest
import respx

@respx.mock
async def test_payment_gateway_timeout_handling():
    # Configure respx to intercept outbound calls to the payment gateway
    payment_route = respx.post("https://api.stripe.internal/v1/charges").mock(
        side_effect=httpx.ConnectTimeout("Connection to gateway timed out.")
    )

    client = PaymentClient(base_url="https://api.stripe.internal")
    
    # Assert that the application circuit breaker catches the timeout and raises custom domain exception
    with pytest.raises(PaymentGatewayUnavailableError):
        await client.charge(amount=100, currency="USD")

    # Assert that the client actually attempted the call with proper authorization headers
    assert payment_route.called
    assert "Bearer" in payment_route.calls.last.request.headers["Authorization"]
