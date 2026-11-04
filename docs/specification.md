# Banking Module Specification

Amounts are in rupees and use `Decimal`, never floats.

## Inputs

| Input | Rule | Error when broken |
|---|---|---|
| Amount | `Decimal`, from 1.00 to 100000.00, at most 2 decimal places | `INVALID_AMOUNT` |
| Amount as text | Digits with an optional 1 or 2 decimals; no signs, commas or exponents | `INVALID_AMOUNT` |
| Owner name | 2 to 50 characters after trimming; letters, spaces, `.`, `'`, `-` | `INVALID_OWNER_NAME` |

## Accounts

| Type | Minimum opening deposit | Balance floor |
|---|---|---|
| Savings | 1,000.00 | 1,000.00 (minimum balance) |
| Current | 5,000.00 | -10,000.00 (overdraft) |

## Operations

| Operation | Rules | Errors |
|---|---|---|
| Open account | Valid name and amount, at least the minimum deposit | `INVALID_OWNER_NAME`, `INVALID_AMOUNT`, `BELOW_OPENING_BALANCE` |
| Deposit | Allowed on active and frozen accounts | `INVALID_AMOUNT`, `ACCOUNT_NOT_FOUND`, `ACCOUNT_CLOSED` |
| Withdraw | Active accounts only. Must not go below the floor. At most 50,000.00 per account per calendar day | `INVALID_AMOUNT`, `ACCOUNT_NOT_FOUND`, `ACCOUNT_FROZEN`, `ACCOUNT_CLOSED`, `DAILY_LIMIT_EXCEEDED`, `INSUFFICIENT_FUNDS` |
| Transfer | Sender must be active; receiver must not be closed. The sender pays the fee, and amount plus fee must not break the floor. All or nothing. Does not count toward the daily limit | `INVALID_AMOUNT`, `ACCOUNT_NOT_FOUND`, `SAME_ACCOUNT_TRANSFER`, `ACCOUNT_FROZEN`, `ACCOUNT_CLOSED`, `INSUFFICIENT_FUNDS` |
| Monthly interest | Savings only. Current accounts earn 0.00. Also accrues on frozen accounts | `ACCOUNT_NOT_FOUND`, `ACCOUNT_CLOSED` |
| Freeze | Active accounts only | `ACCOUNT_NOT_FOUND`, `ACCOUNT_FROZEN`, `ACCOUNT_CLOSED` |
| Unfreeze | Not on closed accounts | `ACCOUNT_NOT_FOUND`, `ACCOUNT_CLOSED` |
| Close | Active accounts only. Pays out a positive balance. Overdrafts must be repaid first | `ACCOUNT_NOT_FOUND`, `ACCOUNT_FROZEN`, `ACCOUNT_CLOSED`, `OUTSTANDING_BALANCE` |

## Transfer fee

| Amount | Fee |
|---|---|
| Up to 10,000.00 | 0.00 |
| 10,000.01 to 50,000.00 | 5.00 |
| Above 50,000.00 | 15.00 |

## Savings interest

| Balance | Yearly rate |
|---|---|
| Below 1,00,000.00 | 3.0% |
| 1,00,000.00 to below 10,00,000.00 | 3.5% |
| 10,00,000.00 and above | 4.0% |

Monthly interest is balance x rate / 12, rounded half-even to 2 decimal places.

## Notifications

Successful money movements send an alert. A failed alert is logged and never undoes the operation. Refused operations send no alert.
