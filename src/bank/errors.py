"""Every way a banking operation can be refused."""

from enum import Enum


class ErrorCode(Enum):
    INVALID_AMOUNT = "INVALID_AMOUNT"
    INVALID_OWNER_NAME = "INVALID_OWNER_NAME"
    BELOW_OPENING_BALANCE = "BELOW_OPENING_BALANCE"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    DAILY_LIMIT_EXCEEDED = "DAILY_LIMIT_EXCEEDED"
    ACCOUNT_NOT_FOUND = "ACCOUNT_NOT_FOUND"
    ACCOUNT_FROZEN = "ACCOUNT_FROZEN"
    ACCOUNT_CLOSED = "ACCOUNT_CLOSED"
    SAME_ACCOUNT_TRANSFER = "SAME_ACCOUNT_TRANSFER"
    OUTSTANDING_BALANCE = "OUTSTANDING_BALANCE"


class BankingError(Exception):
    """Raised when a banking rule refuses an operation. No balance changes when this is raised."""

    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
