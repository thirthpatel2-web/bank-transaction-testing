"""Account state and statements. The business rules live in service.py."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


class AccountType(Enum):
    """The floor is the lowest balance a withdrawal or transfer may leave behind."""

    SAVINGS = (Decimal("1000.00"), Decimal("1000.00"))
    CURRENT = (Decimal("5000.00"), Decimal("-10000.00"))

    @property
    def minimum_opening_deposit(self) -> Decimal:
        return self.value[0]

    @property
    def balance_floor(self) -> Decimal:
        return self.value[1]


class AccountStatus(Enum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    CLOSED = "CLOSED"


class TransactionType(Enum):
    OPENING_DEPOSIT = "OPENING_DEPOSIT"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER_OUT = "TRANSFER_OUT"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_FEE = "TRANSFER_FEE"
    INTEREST = "INTEREST"
    CLOSING_PAYOUT = "CLOSING_PAYOUT"


@dataclass(frozen=True)
class Transaction:
    """One immutable line of an account statement."""

    type: TransactionType
    amount: Decimal
    balance_after: Decimal
    at: datetime


class Account:
    def __init__(self, account_id: str, owner: str, account_type: AccountType) -> None:
        self.id = account_id
        self.owner = owner
        self.type = account_type
        self.balance = Decimal("0.00")
        self.status = AccountStatus.ACTIVE
        self._transactions: list[Transaction] = []
        self._withdrawn_today = Decimal("0.00")
        self._withdrawal_date: date | None = None

    @property
    def transactions(self) -> tuple[Transaction, ...]:
        return tuple(self._transactions)

    def credit(self, tx_type: TransactionType, amount: Decimal, at: datetime) -> None:
        self.balance += amount
        self._transactions.append(Transaction(tx_type, amount, self.balance, at))

    def debit(self, tx_type: TransactionType, amount: Decimal, at: datetime) -> None:
        self.balance -= amount
        self._transactions.append(Transaction(tx_type, amount, self.balance, at))

    def withdrawn_on(self, day: date) -> Decimal:
        """Total withdrawn on the given calendar day."""
        return self._withdrawn_today if day == self._withdrawal_date else Decimal("0.00")

    def record_withdrawal(self, day: date, amount: Decimal) -> None:
        self._withdrawn_today = self.withdrawn_on(day) + amount
        self._withdrawal_date = day
