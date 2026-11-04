# Test Case Matrix

Author is the planned owner: Student A is Thirth Patel, Student B is Vaishnavi V.

Techniques: BVA is boundary value analysis, ECP is equivalence partitioning, NEG is negative validation, TYPE is syntax or type checking, STATE is state-based, MOCK uses a mocked gateway, PBT is property-based.

| Test ID | Scenario | Precondition | Input | Expected result | Technique | Author |
|---|---|---|---|---|---|---|
| TC-VAL-01 to 05 | Amounts at and inside the limits | None | 1.00, 1.01, 50000.00, 99999.99, 100000.00 | Accepted | BVA | B |
| TC-VAL-06 | Trailing zero is not an extra decimal | None | 5.000 | Accepted | ECP | B |
| TC-VAL-07 to 08 | Just outside the limits | None | 0.99, 100000.01 | `INVALID_AMOUNT` | BVA | B |
| TC-VAL-09 to 11 | Zero, negative, too many decimals | None | 0.00, -1.00, 1.005 | `INVALID_AMOUNT` | NEG | B |
| TC-VAL-12 to 18 | Wrong types and non-finite values | None | None, float, str, int, bool, NaN, Infinity | `INVALID_AMOUNT` | TYPE | B |
| TC-VAL-19 to 21 | Valid amount text | None | "250", "250.5", " 99.99 " | 250.00, 250.50, 99.99 | ECP | B |
| TC-VAL-22 | Invalid amount text | None | "abc", "1e3", "-5", "12.345", "1,000", "0.50", "100000.01", "12.", ".5", spaces, empty, "NaN", Arabic digits, None, 12 | `INVALID_AMOUNT` | TYPE | B |
| TC-VAL-23 to 29 | Name length limits | None | Lengths 1, 2, 3, 25, 49, 50, 51 | 1 and 51 refused, others accepted | BVA | B |
| TC-VAL-30 | Realistic names | None | "Thirth Patel", "O'Brien", "Anne-Marie", "Dr. Rao", padded name | Accepted | ECP | B |
| TC-VAL-31 | Invalid names | None | "R2D2", "user@bank", "<script>", spaces, "under_score", None, 42 | `INVALID_OWNER_NAME` | NEG | B |
| TC-FEE-01 to 08 | Fee tier limits | None | 1.00, 9999.99, 10000.00, 10000.01, 49999.99, 50000.00, 50000.01, 100000.00 | 0, 0, 0, 5, 5, 5, 15, 15 | BVA | B |
| TC-INT-01 to 06 | Rate slab limits | None | 99999.99, 100000.00, 100000.01, 999999.99, 1000000.00, 1000000.01 | 3.0, 3.5, 3.5, 3.5, 4.0, 4.0% | BVA | B |
| TC-INT-07 to 09 | Monthly interest in each slab | None | 12000, 100000, 1000000 | 30.00, 291.67, 3333.33 | ECP | B |
| TC-INT-10, 11, 14 | Nothing on zero or overdrawn balances | None | 0.00, -500.00, -0.50 | 0.00 | BVA | B |
| TC-INT-12 to 13 | Half-even rounding | None | 1002.00, 1006.00 | 2.50, 2.52 | BVA | A |
| TC-OPN-01 to 04 | Minimum opening deposit | None | Savings 1000.00, 999.99; Current 5000.00, 4999.99 | Opened, `BELOW_OPENING_BALANCE`, opened, `BELOW_OPENING_BALANCE` | BVA | B |
| TC-OPN-05 to 06 | Maximum opening deposit | None | 100000.00, 100000.01 | Opened, `INVALID_AMOUNT` | BVA | B |
| TC-OPN-07 | Ids and trimmed name | None | "  Thirth Patel " plus a second account | ACC-0001, ACC-0002, trimmed, active | ECP | A |
| TC-OPN-08 | Refused opening has no effect | None | "R2D2" | `INVALID_OWNER_NAME`, no account, no alert | NEG, MOCK | A |
| TC-DEP-01 | Normal deposit | Balance 1000.00 | 250.50 | Balance 1250.50 | ECP | A |
| TC-DEP-02 to 03 | Out of range deposit | Balance 1000.00 | 0.99, 100000.01 | `INVALID_AMOUNT`, balance unchanged | BVA | A |
| TC-DEP-04 | Unknown account | None | ACC-9999 | `ACCOUNT_NOT_FOUND` | NEG | A |
| TC-DEP-05 to 06 | Deposit by account state | Frozen; closed | 100.00 | Accepted; `ACCOUNT_CLOSED` | STATE | A |
| TC-WD-01 to 04 | Savings floor | Balance 10000.00 | 8999.99, 9000.00, 9000.01, 1.00 | 1000.01, 1000.00, `INSUFFICIENT_FUNDS`, 9999.00 | BVA | A |
| TC-WD-05 to 08 | Current overdraft floor | Balance 10000.00 | 19999.99, 20000.00, 20000.01, 10000.00 | -9999.99, -10000.00, `INSUFFICIENT_FUNDS`, 0.00 | BVA | A |
| TC-WD-09 | Invalid amount | Balance 10000.00 | 0.99 | `INVALID_AMOUNT` | NEG | A |
| TC-WD-10 to 11 | Withdrawal by account state | Frozen; closed | 100.00 | `ACCOUNT_FROZEN`; `ACCOUNT_CLOSED` | STATE | A |
| TC-LIM-01 to 02 | Daily limit | Balance 200000.00 | 30000 + 20000; 30000 + 20000.01 | Accepted; `DAILY_LIMIT_EXCEEDED` | BVA | A |
| TC-LIM-03 to 04 | Limit at midnight | 50000 withdrawn at 23:59:59 | 1.00 same second; 50000 one second later | `DAILY_LIMIT_EXCEEDED`; accepted | BVA | A |
| TC-LIM-05 | Refused withdrawal not counted | Balance 20000.00 | 40000 refused, then deposit and 50000 | Accepted | STATE | A |
| TC-LIM-06 | Limit is per account | Two accounts | 50000 from each | Both accepted | ECP | A |
| TC-TRF-01 to 02 | Fee charged to sender only | Sender 20000, receiver 5000 | 10000.00, 10000.01 | Fee 0 and 5, receiver gets the exact amount | ECP | A |
| TC-TRF-03 to 06 | Fee included in funds check | Savings sender | 11000/10000.00, 11000/10000.01, 11005.01/10000.01, 11005.00/10000.01 | OK, refused, OK, refused | BVA | A |
| TC-TRF-07 to 08 | Overdraft with fee | Current sender 5000.00 | 14995.00, 14995.01 | -10000.00, `INSUFFICIENT_FUNDS` | BVA | A |
| TC-TRF-09 | Same account | Active account | Same id twice | `SAME_ACCOUNT_TRANSFER` | NEG | A |
| TC-TRF-10 to 11 | Out of range transfer | Active accounts | 0.99, 100000.01 | `INVALID_AMOUNT` | BVA | A |
| TC-TRF-12 to 14 | Unknown or missing ids | Active accounts | ACC-9999 as source; as destination; None as source | `ACCOUNT_NOT_FOUND`, balance unchanged | NEG | A |
| TC-TRF-15 to 16 | Frozen accounts | Sender frozen; receiver frozen | 100.00 | `ACCOUNT_FROZEN`; accepted | STATE | A |
| TC-TRF-17 | Closed receiver loses no money | Receiver closed | 1000.00 | `ACCOUNT_CLOSED`, sender unchanged, no statement line | STATE | A |
| TC-TRF-18 | Transfers skip the daily limit | Balance 100000.00 | Transfer 60000, then withdraw 30000 | Both accepted | ECP | A |
| TC-TRF-19 | Same account compared by value | Active account | Equal id held as a separate string | `SAME_ACCOUNT_TRANSFER` | NEG | A |
| TC-MI-01 to 04 | Interest by type and state | Savings; current; frozen; closed | Apply interest | 30.00; 0.00; 30.00; `ACCOUNT_CLOSED` | STATE | A |
| TC-LIF-01 to 04 | Freeze and close transitions | Various | Freeze, unfreeze, close | Allowed or refused per specification | STATE | A |
| TC-LIF-05 | Overdrawn account | Balance -1000.00 | Close | `OUTSTANDING_BALANCE` | NEG | A |
| TC-LIF-06 | Savings close with payout | Balance 1000.00 | Close | Closed, balance 0.00, payout line | STATE | A |
| TC-LIF-07 | Unknown account | None | ACC-9999 | `ACCOUNT_NOT_FOUND` | NEG | A |
| TC-LIF-08 | Overdrawn by paise | Balance -0.50 | Close | `OUTSTANDING_BALANCE` | BVA | A |
| TC-LIF-09 | Balance under one rupee | Balance 0.50 | Close | Closed, balance 0.00, payout line | BVA | A |
| TC-LIF-10 | Zero balance close | Balance 0.00 | Close | Closed, no payout line | BVA | A |
| TC-STM-01 to 02 | Statement contents and immutability | Balance 5000.00 | Withdraw 500.00; edit a line | Correct line; edit refused | ECP | A |
| TC-NOT-01 to 05 | Alerts, including a gateway outage | Mocked gateway | Various | Exact alerts; outage keeps the money movement | MOCK | A |
| TC-REP-01 to 02 | Repository lookups | None | Saved id; unknown id | Account; None | ECP | A |
| TC-PBT-01 to 03 | Validator never misbehaves | None | Generated amounts and text | Accepted or a clean refusal | PBT | A |
| TC-PBT-04 to 05 | Money is conserved; floor never broken | Generated accounts | Generated transfers and operation sequences | Invariants hold | PBT | A |
