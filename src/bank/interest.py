"""Savings interest slabs by balance.

Below 1,00,000 earns 3.0% a year, from 1,00,000 earns 3.5%, from 10,00,000 earns 4.0%.
One month is a twelfth of the yearly rate, rounded half-even to paise.
"""

from decimal import ROUND_HALF_EVEN, Decimal

MID_SLAB_START = Decimal("100000.00")
TOP_SLAB_START = Decimal("1000000.00")
BASE_RATE = Decimal("0.030")
MID_RATE = Decimal("0.035")
TOP_RATE = Decimal("0.040")


def annual_rate(balance: Decimal) -> Decimal:
    if balance >= TOP_SLAB_START:
        return TOP_RATE
    if balance >= MID_SLAB_START:
        return MID_RATE
    return BASE_RATE


def monthly_interest(balance: Decimal) -> Decimal:
    if balance <= 0:
        return Decimal("0.00")
    return (balance * annual_rate(balance) / 12).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
