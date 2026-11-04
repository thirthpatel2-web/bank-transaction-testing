"""Transfer fee tiers: up to 10,000 free, up to 50,000 costs 5.00, above that 15.00."""

from decimal import Decimal

FREE_LIMIT = Decimal("10000.00")
STANDARD_LIMIT = Decimal("50000.00")
STANDARD_FEE = Decimal("5.00")
HIGH_VALUE_FEE = Decimal("15.00")


def transfer_fee(amount: Decimal) -> Decimal:
    if amount <= FREE_LIMIT:
        return Decimal("0.00")
    if amount <= STANDARD_LIMIT:
        return STANDARD_FEE
    return HIGH_VALUE_FEE
