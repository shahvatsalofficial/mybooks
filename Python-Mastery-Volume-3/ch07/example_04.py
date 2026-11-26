def test_money_addition():
    assert Money("10.00", "USD") + Money("5.00", "USD") == Money("15.00", "USD")
