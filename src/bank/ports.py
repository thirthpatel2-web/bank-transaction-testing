"""Boundaries to the outside world: account storage and outbound alerts."""

from typing import Protocol

from bank.models import Account


class NotificationGateway(Protocol):
    """Outbound SMS/email alerts. Replaced by a mock in tests."""

    def send(self, account_id: str, message: str) -> None: ...


class AccountRepository(Protocol):
    def save(self, account: Account) -> None: ...

    def find_by_id(self, account_id: str) -> Account | None: ...


class InMemoryAccountRepository:
    def __init__(self) -> None:
        self._accounts: dict[str, Account] = {}

    def save(self, account: Account) -> None:
        self._accounts[account.id] = account

    def find_by_id(self, account_id: str) -> Account | None:
        return self._accounts.get(account_id)
