"""Property-based tests: Hypothesis generates inputs and checks rules that must always hold."""

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from bank.errors import BankingError, ErrorCode
from bank.fees import transfer_fee
from bank.models import AccountType
from bank.validation import parse_amount, validate_amount
from support import make_bank

pytestmark = pytest.mark.property

valid_amounts = st.decimals(min_value=Decimal("1.00"), max_value=Decimal("100000.00"), places=2)
account_types = st.sampled_from(list(AccountType))
openings = st.decimals(min_value=Decimal("5000.00"), max_value=Decimal("100000.00"), places=2)


@given(valid_amounts)
def test_TC_PBT_01_every_two_decimal_amount_in_range_is_valid(amount):
    validate_amount(amount)
    assert parse_amount(str(amount)) == amount


@given(st.text(max_size=40))
def test_TC_PBT_02_text_parsing_only_ever_refuses_cleanly(text):
    try:
        assert Decimal("1.00") <= parse_amount(text) <= Decimal("100000.00")
    except BankingError as refusal:
        assert refusal.code is ErrorCode.INVALID_AMOUNT


@given(st.from_regex(r"[0-9]{1,60}(\.[0-9]{1,2})?", fullmatch=True))
def test_TC_PBT_03_numeric_text_of_any_length_only_ever_refuses_cleanly(text):
    try:
        assert Decimal("1.00") <= parse_amount(text) <= Decimal("100000.00")
    except BankingError as refusal:
        assert refusal.code is ErrorCode.INVALID_AMOUNT


@given(account_types, account_types, openings, openings, valid_amounts)
def test_TC_PBT_04_a_transfer_conserves_money_apart_from_the_fee(type_a, type_b, opening_a, opening_b, amount):
    bank = make_bank()
    sender = bank.open_account("Test Customer", type_a, opening_a)
    receiver = bank.open_account("Test Customer", type_b, opening_b)
    try:
        bank.transfer(sender.id, receiver.id, amount)
    except BankingError:
        assert (sender.balance, receiver.balance) == (opening_a, opening_b)
    else:
        assert sender.balance == opening_a - amount - transfer_fee(amount)
        assert receiver.balance == opening_b + amount


operations = st.lists(
    st.tuples(st.sampled_from(["deposit", "withdraw", "transfer", "interest"]), valid_amounts),
    max_size=25,
)


@settings(max_examples=200)
@given(account_types, operations)
def test_TC_PBT_05_no_operation_sequence_breaks_the_balance_floor(account_type, steps):
    bank = make_bank()
    account = bank.open_account("Test Customer", account_type, Decimal("50000.00"))
    other = bank.open_account("Test Customer", AccountType.SAVINGS, Decimal("50000.00"))
    actions = {
        "deposit": lambda amount: bank.deposit(account.id, amount),
        "withdraw": lambda amount: bank.withdraw(account.id, amount),
        "transfer": lambda amount: bank.transfer(account.id, other.id, amount),
        "interest": lambda amount: bank.apply_monthly_interest(account.id),
    }
    for name, amount in steps:
        try:
            actions[name](amount)
        except BankingError:
            pass
        assert account.balance >= account_type.balance_floor
