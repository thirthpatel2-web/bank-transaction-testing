from decimal import Decimal

import pytest

from bank.fees import transfer_fee
from bank.interest import annual_rate, monthly_interest


@pytest.mark.boundary
@pytest.mark.parametrize(
    ("amount", "expected_fee"),
    [
        pytest.param("1.00", "0.00", id="TC-FEE-01"),
        pytest.param("9999.99", "0.00", id="TC-FEE-02"),
        pytest.param("10000.00", "0.00", id="TC-FEE-03"),
        pytest.param("10000.01", "5.00", id="TC-FEE-04"),
        pytest.param("49999.99", "5.00", id="TC-FEE-05"),
        pytest.param("50000.00", "5.00", id="TC-FEE-06"),
        pytest.param("50000.01", "15.00", id="TC-FEE-07"),
        pytest.param("100000.00", "15.00", id="TC-FEE-08"),
    ],
)
def test_fee_tiers(amount, expected_fee):
    assert transfer_fee(Decimal(amount)) == Decimal(expected_fee)


@pytest.mark.boundary
@pytest.mark.parametrize(
    ("balance", "expected_rate"),
    [
        pytest.param("99999.99", "0.030", id="TC-INT-01"),
        pytest.param("100000.00", "0.035", id="TC-INT-02"),
        pytest.param("100000.01", "0.035", id="TC-INT-03"),
        pytest.param("999999.99", "0.035", id="TC-INT-04"),
        pytest.param("1000000.00", "0.040", id="TC-INT-05"),
        pytest.param("1000000.01", "0.040", id="TC-INT-06"),
    ],
)
def test_rate_slabs(balance, expected_rate):
    assert annual_rate(Decimal(balance)) == Decimal(expected_rate)


@pytest.mark.parametrize(
    ("balance", "expected"),
    [
        pytest.param("12000.00", "30.00", id="TC-INT-07"),
        pytest.param("100000.00", "291.67", id="TC-INT-08"),
        pytest.param("1000000.00", "3333.33", id="TC-INT-09"),
        pytest.param("0.00", "0.00", id="TC-INT-10-zero"),
        pytest.param("-500.00", "0.00", id="TC-INT-11-overdrawn"),
        pytest.param("1002.00", "2.50", id="TC-INT-12-half-even-down"),
        pytest.param("1006.00", "2.52", id="TC-INT-13-half-even-up"),
        pytest.param("-0.50", "0.00", id="TC-INT-14-slightly-overdrawn"),
    ],
)
def test_monthly_interest(balance, expected):
    assert monthly_interest(Decimal(balance)) == Decimal(expected)
