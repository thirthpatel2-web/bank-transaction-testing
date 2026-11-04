"""Banking operations: opening accounts, deposits, withdrawals, transfers, interest and lifecycle."""

import logging
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal

from bank.errors import BankingError, ErrorCode
from bank.fees import transfer_fee
from bank.interest import monthly_interest
from bank.models import Account, AccountStatus, AccountType, TransactionType
from bank.ports import AccountRepository, NotificationGateway
from bank.validation import validate_amount, validate_owner_name

DAILY_WITHDRAWAL_LIMIT = Decimal("50000.00")

logger = logging.getLogger(__name__)


class BankingService:
    def __init__(
        self,
        repository: AccountRepository,
        notifier: NotificationGateway,
        clock: Callable[[], datetime],
    ) -> None:
        self._repository = repository
        self._notifier = notifier
        self._clock = clock
        self._next_account_number = 1

    def open_account(self, owner: str, account_type: AccountType, opening_deposit: Decimal) -> Account:
        validate_owner_name(owner)
        validate_amount(opening_deposit)
        if opening_deposit < account_type.minimum_opening_deposit:
            raise BankingError(
                ErrorCode.BELOW_OPENING_BALANCE,
                f"{account_type.name} needs at least {account_type.minimum_opening_deposit}",
            )
        account = Account(f"ACC-{self._next_account_number:04d}", owner.strip(), account_type)
        self._next_account_number += 1
        account.credit(TransactionType.OPENING_DEPOSIT, opening_deposit, self._clock())
        self._repository.save(account)
        self._notify(account.id, "Account opened")
        return account

    def deposit(self, account_id: str, amount: Decimal) -> Decimal:
        validate_amount(amount)
        account = self.get_account(account_id)
        self._require_not_closed(account)
        account.credit(TransactionType.DEPOSIT, amount, self._clock())
        self._repository.save(account)
        self._notify(account_id, f"Deposited {amount}")
        return account.balance

    def withdraw(self, account_id: str, amount: Decimal) -> Decimal:
        validate_amount(amount)
        account = self.get_account(account_id)
        self._require_active(account)
        now = self._clock()
        if account.withdrawn_on(now.date()) + amount > DAILY_WITHDRAWAL_LIMIT:
            raise BankingError(ErrorCode.DAILY_LIMIT_EXCEEDED, "Daily withdrawal limit exceeded")
        if account.balance - amount < account.type.balance_floor:
            raise BankingError(ErrorCode.INSUFFICIENT_FUNDS, "Withdrawal would pass the balance floor")
        account.debit(TransactionType.WITHDRAWAL, amount, now)
        account.record_withdrawal(now.date(), amount)
        self._repository.save(account)
        self._notify(account_id, f"Withdrew {amount}")
        return account.balance

    def transfer(self, from_id: str, to_id: str, amount: Decimal) -> None:
        """Moves money and charges the tiered fee to the sender. Either everything happens or nothing does."""
        validate_amount(amount)
        sender = self.get_account(from_id)
        receiver = self.get_account(to_id)
        if from_id == to_id:
            raise BankingError(ErrorCode.SAME_ACCOUNT_TRANSFER, "Cannot transfer to the same account")
        self._require_active(sender)
        self._require_not_closed(receiver)

        fee = transfer_fee(amount)
        if sender.balance - amount - fee < sender.type.balance_floor:
            raise BankingError(ErrorCode.INSUFFICIENT_FUNDS, "Transfer would pass the balance floor")

        now = self._clock()
        sender.debit(TransactionType.TRANSFER_OUT, amount, now)
        if fee > 0:
            sender.debit(TransactionType.TRANSFER_FEE, fee, now)
        receiver.credit(TransactionType.TRANSFER_IN, amount, now)
        self._repository.save(sender)
        self._repository.save(receiver)
        self._notify(from_id, f"Sent {amount} with fee {fee}")
        self._notify(to_id, f"Received {amount}")

    def apply_monthly_interest(self, account_id: str) -> Decimal:
        """Credits one month of interest to a savings account. Current accounts earn none."""
        account = self.get_account(account_id)
        self._require_not_closed(account)
        if account.type is not AccountType.SAVINGS:
            return Decimal("0.00")
        interest = monthly_interest(account.balance)
        account.credit(TransactionType.INTEREST, interest, self._clock())
        self._repository.save(account)
        self._notify(account_id, f"Interest credited {interest}")
        return interest

    def freeze(self, account_id: str) -> None:
        account = self.get_account(account_id)
        self._require_active(account)
        account.status = AccountStatus.FROZEN
        self._repository.save(account)

    def unfreeze(self, account_id: str) -> None:
        account = self.get_account(account_id)
        self._require_not_closed(account)
        account.status = AccountStatus.ACTIVE
        self._repository.save(account)

    def close(self, account_id: str) -> None:
        """Closes an active account and pays out any balance. An overdrawn account must be repaid first."""
        account = self.get_account(account_id)
        self._require_active(account)
        if account.balance < 0:
            raise BankingError(ErrorCode.OUTSTANDING_BALANCE, "Overdraft must be repaid before closing")
        if account.balance > 0:
            account.debit(TransactionType.CLOSING_PAYOUT, account.balance, self._clock())
        account.status = AccountStatus.CLOSED
        self._repository.save(account)

    def get_account(self, account_id: str) -> Account:
        account = self._repository.find_by_id(account_id)
        if account is None:
            raise BankingError(ErrorCode.ACCOUNT_NOT_FOUND, f"No account {account_id}")
        return account

    def _require_active(self, account: Account) -> None:
        self._require_not_closed(account)
        if account.status is AccountStatus.FROZEN:
            raise BankingError(ErrorCode.ACCOUNT_FROZEN, f"Account is frozen: {account.id}")

    def _require_not_closed(self, account: Account) -> None:
        if account.status is AccountStatus.CLOSED:
            raise BankingError(ErrorCode.ACCOUNT_CLOSED, f"Account is closed: {account.id}")

    def _notify(self, account_id: str, message: str) -> None:
        """A failed alert must never undo a completed money movement."""
        try:
            self._notifier.send(account_id, message)
        except Exception:
            logger.warning("Notification failed for %s", account_id, exc_info=True)
