"""Input checks that run before any account is touched."""

import re
from decimal import Decimal

from bank.errors import BankingError, ErrorCode

MIN_AMOUNT = Decimal("1.00")
MAX_AMOUNT = Decimal("100000.00")
MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 50

_AMOUNT_SYNTAX = re.compile(r"[0-9]+(\.[0-9]{1,2})?")
_NAME_SYNTAX = re.compile(r"(?:[^\W\d_]|[ .'-])+")


def validate_amount(amount: Decimal) -> None:
    """An amount must be a Decimal from 1.00 to 100000.00 with at most two decimal places."""
    if not isinstance(amount, Decimal) or not amount.is_finite():
        raise BankingError(ErrorCode.INVALID_AMOUNT, f"Not a valid amount: {amount!r}")
    if amount.normalize().as_tuple().exponent < -2:
        raise BankingError(ErrorCode.INVALID_AMOUNT, f"At most two decimal places: {amount}")
    if amount < MIN_AMOUNT or amount > MAX_AMOUNT:
        raise BankingError(ErrorCode.INVALID_AMOUNT, f"Amount out of range: {amount}")


def parse_amount(text: str) -> Decimal:
    """Converts user-entered text to an amount, rejecting anything that is not plain decimal money."""
    if not isinstance(text, str) or not _AMOUNT_SYNTAX.fullmatch(text.strip()):
        raise BankingError(ErrorCode.INVALID_AMOUNT, f"Not a valid amount: {text!r}")
    amount = Decimal(text.strip())
    validate_amount(amount)
    return amount.quantize(Decimal("0.01"))


def validate_owner_name(name: str) -> None:
    """A name must be 2 to 50 characters after trimming: letters, spaces, dots, apostrophes or hyphens."""
    if not isinstance(name, str):
        raise BankingError(ErrorCode.INVALID_OWNER_NAME, "Owner name is required")
    trimmed = name.strip()
    if not MIN_NAME_LENGTH <= len(trimmed) <= MAX_NAME_LENGTH:
        raise BankingError(ErrorCode.INVALID_OWNER_NAME, "Owner name length out of range")
    if not _NAME_SYNTAX.fullmatch(trimmed):
        raise BankingError(ErrorCode.INVALID_OWNER_NAME, "Owner name has invalid characters")
