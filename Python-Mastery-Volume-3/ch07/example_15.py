# Deterministic time testing with time-machine
import datetime
import time_machine

def test_subscription_trial_expiration():
    # Freeze time at a deterministic UTC epoch
    with time_machine.travel(datetime.datetime(2026, 10, 19, 12, 0, 0, tzinfo=datetime.timezone.utc)):
        subscription = UserSubscription(trial_days=14)
        assert subscription.is_active is True

        # Fast-forward 15 days into the future instantaneously
        time_machine.coordinates.shift(datetime.timedelta(days=15))
        assert subscription.is_active is False
