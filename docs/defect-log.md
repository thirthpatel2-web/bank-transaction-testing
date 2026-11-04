# Defect Log

The first test run was against a version containing these defects: 9 failed, 141 passed. Evidence is in `docs/evidence/01-before-fixes-run.log`, and the fixes are in `docs/defects/fixes.diff`.

**Seeded** defects were placed on purpose to evaluate the test suite. **Design gap** is a real mistake in the first draft of the rules, noticed while designing the tests and left in so the suite could confirm it.

| ID | Origin | Severity | Priority | Defect | Caught by | Root cause | Fix |
|---|---|---|---|---|---|---|---|
| D1 | Seeded | Medium | P2 | A withdrawal landing exactly on the balance floor is refused | TC-WD-02, TC-WD-06 | `<=` used instead of `<` | Use `<` |
| D2 | Seeded | Critical | P1 | A transfer to a closed account is refused but the sender still loses the money | TC-TRF-17 | Receiver checked after the sender is debited | Check before any debit |
| D3 | Seeded | High | P1 | A transfer fee can push the sender below the balance floor | TC-TRF-06, TC-TRF-08 | Funds check ignores the fee | Include the fee in the check |
| D4 | Seeded | Medium | P2 | A balance of exactly 1,00,000 earns 3.0% instead of 3.5% | TC-INT-02, TC-INT-08 | `>` used instead of `>=` | Use `>=` |
| D5 | Seeded | High | P1 | The daily withdrawal limit never resets, blocking later days | TC-LIM-04 | The withdrawn total ignores the date | Count only the current day |
| D6 | Design gap | High | P2 | A savings account can never be closed | TC-LIF-06 | Closing needs a zero balance, but withdrawals stop at the 1,000 floor | Closing pays out the balance |

## Steps to reproduce (D2, the most severe)

1. Open a savings account with 20,000.00.
2. Open a current account, withdraw its full 5,000.00, and close it.
3. Transfer 1,000.00 from the savings account to the closed account.
4. Expected: `ACCOUNT_CLOSED`, with the sender still at 20,000.00.
5. Actual before the fix: `ACCOUNT_CLOSED`, with the sender at 19,000.00.

## Test gaps found by mutation testing

These are weaknesses in the tests, not bugs in the module. All tests were passing with 100% statement and branch coverage when Cosmic Ray found them.

| Run | Tests | Mutants | Killed | Survived | Score |
|---|---|---|---|---|---|
| First (`docs/evidence/03a-mutation-first-run.txt`) | 150 | 316 | 301 | 15 | 95.3% |
| After adding tests (`docs/evidence/03b-mutation-final-run.txt`) | 155 | 316 | 307 | 9 | 97.2% |

The tests below killed 6 of the 15 survivors.

| Gap | Surviving change | Test added |
|---|---|---|
| Same-account check only tested with the same string object | `==` changed to `is` | TC-TRF-19 |
| Log details for gateway failures not checked | `exc_info=True` changed to `False` | Extended TC-NOT-04 |
| Overdraft check not tested for under one rupee | `< 0` changed to `< -1` | TC-LIF-08 |
| Payout not tested for under one rupee | `> 0` changed to `> 1` | TC-LIF-09 |
| Zero balance close not checked for a stray payout line | `> 0` changed to `> -1` and `>= 0` | TC-LIF-10 |

## The 9 remaining survivors

We reviewed each by hand and found no input that makes these changes behave differently, so no test can kill them.

| Location | Change | Why behavior stays the same |
|---|---|---|
| `interest.py` line 25 | `<= 0` to `< 0` | Interest on a zero balance is 0.00 either way |
| `interest.py` line 25 | `<= 0` to `<= -1` | A balance between -1 and 0 rounds to 0.00 interest (TC-INT-14 confirms this) |
| `interest.py` line 25 | `<= 0` to `<= 1` | A balance from 0 to 1 rounds to 0.00 interest |
| `service.py` line 87 | `fee > 0` to `fee > 1` | Fees are only 0, 5 or 15 |
| `service.py` line 87 | `fee > 0` to `fee != 0` | Fees are never negative |
| `service.py` line 99 | `is not` to `!=` | Enum members are unique objects |
| `service.py` line 125 | `> 0` to `!= 0` | Negative balances were already refused above |
| `service.py` line 138 | `is` to `==` | Enum members are unique objects |
| `service.py` line 142 | `is` to `==` | Enum members are unique objects |

## Observation: property tests did not catch the seeded defects

All 5 Hypothesis tests passed on the defective version. Every failure came from hand-designed boundary and state tests. Random inputs rarely land on an exact limit, so generated data adds to boundary analysis rather than replacing it.
