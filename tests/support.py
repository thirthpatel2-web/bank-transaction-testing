"""Helpers shared by the test modules."""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock

import pytest

from bank.errors import BankingError, ErrorCode
from bank.models import Account, AccountType
from bank.ports import InMemoryAccountRepository
from bank.service import BankingService

START = datetime(2026, 11, 4, 10, 0, 0)


class MutableClock:
    """A clock tests can move forward, so day-boundary rules run without real waiting."""

    def __init__(self, start: datetime = START) -> None:
        self.now = start

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **kwargs) -> None:
        self.now += timedelta(**kwargs)


def money(value: str) -> Decimal:
    return Decimal(value)


def make_bank(notifier=None, clock=None) -> BankingService:
    return BankingService(InMemoryAccountRepository(), notifier or Mock(), clock or MutableClock())


def open_account(bank: BankingService, account_type: AccountType, deposit: str) -> Account:
    return bank.open_account("Test Customer", account_type, money(deposit))


def closed_account(bank: BankingService) -> Account:
    """A current account can be drained to zero and closed."""
    account = open_account(bank, AccountType.CURRENT, "5000.00")
    bank.withdraw(account.id, money("5000.00"))
    bank.close(account.id)
    return account


def assert_refused(expected: ErrorCode, call, *args) -> None:
    with pytest.raises(BankingError) as refusal:
        call(*args)
    assert refusal.value.code is expected
