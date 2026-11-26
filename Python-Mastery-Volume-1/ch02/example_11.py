from typing import assert_never

def handle_payment_lifecycle(event: PaymentEvent) -> None:
    match event:
        case PaymentInitiated(payment_id=pid, amount_usd=amt):
            logger.info(f"Initiating payment {pid} for ${amt:.2f}")
        case PaymentAuthorized(payment_id=pid, auth_token=token):
            logger.info(f"Payment {pid} authorized with token {token}")
        case PaymentSettled(payment_id=pid, settled_at_epoch=epoch):
            logger.info(f"Payment {pid} settled at {epoch}")
        case PaymentFailed(payment_id=pid, decline_code=code):
            logger.error(f"Payment {pid} declined with code {code}")
        case _ as unreachable:
            # If all cases of PaymentEvent are covered, 'unreachable' is inferred as Never!
            # If a new event is added to PaymentEvent, Mypy triggers a blocking compile error:
            # error: Argument 1 to "assert_never" has incompatible type "PaymentRefunded"; expected "Never"
            assert_never(unreachable)
