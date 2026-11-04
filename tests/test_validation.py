from decimal import Decimal

import pytest

from bank.errors import ErrorCode
from bank.validation import parse_amount, validate_amount, validate_owner_name
from support import assert_refused


@pytest.mark.boundary
@pytest.mark.parametrize(
    "amount",
    [
        pytest.param("1.00", id="TC-VAL-01-min"),
        pytest.param("1.01", id="TC-VAL-02-min-plus-1"),
        pytest.param("50000.00", id="TC-VAL-03-nominal"),
        pytest.param("99999.99", id="TC-VAL-04-max-minus-1"),
        pytest.param("100000.00", id="TC-VAL-05-max"),
        pytest.param("5.000", id="TC-VAL-06-trailing-zero"),
    ],
)
def test_accepts_amounts_in_range(amount):
    validate_amount(Decimal(amount))


@pytest.mark.boundary
@pytest.mark.parametrize(
    "amount",
    [
        pytest.param("0.99", id="TC-VAL-07-min-minus-1"),
        pytest.param("100000.01", id="TC-VAL-08-max-plus-1"),
        pytest.param("0.00", id="TC-VAL-09-zero"),
        pytest.param("-1.00", id="TC-VAL-10-negative"),
        pytest.param("1.005", id="TC-VAL-11-three-decimals"),
    ],
)
def test_rejects_amounts_out_of_range(amount):
    assert_refused(ErrorCode.INVALID_AMOUNT, validate_amount, Decimal(amount))


@pytest.mark.negative
@pytest.mark.parametrize(
    "amount",
    [
        pytest.param(None, id="TC-VAL-12-none"),
        pytest.param(100.5, id="TC-VAL-13-float"),
        pytest.param("100.00", id="TC-VAL-14-string"),
        pytest.param(100, id="TC-VAL-15-int"),
        pytest.param(True, id="TC-VAL-16-bool"),
        pytest.param(Decimal("NaN"), id="TC-VAL-17-nan"),
        pytest.param(Decimal("Infinity"), id="TC-VAL-18-infinity"),
    ],
)
def test_rejects_wrong_types(amount):
    assert_refused(ErrorCode.INVALID_AMOUNT, validate_amount, amount)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param("250", "250.00", id="TC-VAL-19-whole"),
        pytest.param("250.5", "250.50", id="TC-VAL-20-one-decimal"),
        pytest.param(" 99.99 ", "99.99", id="TC-VAL-21-spaces"),
    ],
)
def test_parses_valid_text(text, expected):
    parsed = parse_amount(text)
    assert parsed == Decimal(expected)
    assert parsed.as_tuple().exponent == -2


@pytest.mark.negative
@pytest.mark.parametrize(
    "text",
    ["abc", "1e3", "-5", "12.345", "1,000", "0.50", "100000.01", "12.", ".5", "   ", "", "NaN", "٣٤", None, 12],
    ids=lambda value: f"TC-VAL-22-{value!r}",
)
def test_rejects_bad_text(text):
    assert_refused(ErrorCode.INVALID_AMOUNT, parse_amount, text)


@pytest.mark.boundary
@pytest.mark.parametrize(
    ("length", "valid"),
    [
        pytest.param(1, False, id="TC-VAL-23-len-1"),
        pytest.param(2, True, id="TC-VAL-24-len-2"),
        pytest.param(3, True, id="TC-VAL-25-len-3"),
        pytest.param(25, True, id="TC-VAL-26-len-25"),
        pytest.param(49, True, id="TC-VAL-27-len-49"),
        pytest.param(50, True, id="TC-VAL-28-len-50"),
        pytest.param(51, False, id="TC-VAL-29-len-51"),
    ],
)
def test_name_length_boundaries(length, valid):
    name = "a" * length
    if valid:
        validate_owner_name(name)
    else:
        assert_refused(ErrorCode.INVALID_OWNER_NAME, validate_owner_name, name)


@pytest.mark.parametrize(
    "name",
    ["Thirth Patel", "O'Brien", "Anne-Marie", "Dr. Rao", "  Vaishnavi V  "],
    ids=lambda value: f"TC-VAL-30-{value.strip()}",
)
def test_accepts_realistic_names(name):
    validate_owner_name(name)


@pytest.mark.negative
@pytest.mark.parametrize(
    "name",
    ["R2D2", "user@bank", "<script>", "    ", "under_score", None, 42],
    ids=lambda value: f"TC-VAL-31-{value!r}",
)
def test_rejects_bad_names(name):
    assert_refused(ErrorCode.INVALID_OWNER_NAME, validate_owner_name, name)
