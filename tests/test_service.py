import csv
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import ANY

import pytest

from bank.errors import ErrorCode
from bank.models import AccountStatus, AccountType, Transaction, TransactionType
from bank.ports import InMemoryAccountRepository
from support import START, assert_refused, closed_account, money, open_account

SAVINGS = AccountType.SAVINGS
CURRENT = AccountType.CURRENT


def withdrawal_cases():
    path = Path(__file__).parent / "data" / "withdrawal_boundaries.csv"
    with path.open(encoding="utf-8", newline="") as file:
        return [pytest.param(row, id=row["test_id"]) for row in csv.DictReader(file)]


def tx_types(account):
    return [tx.type for tx in account.transactions]


class TestOpening:
    @pytest.mark.boundary
    @pytest.mark.parametrize(
        ("account_type", "deposit", "outcome"),
        [
            pytest.param(SAVINGS, "1000.00", "OK", id="TC-OPN-01"),
            pytest.param(SAVINGS, "999.99", "BELOW_OPENING_BALANCE", id="TC-OPN-02"),
            pytest.param(CURRENT, "5000.00", "OK", id="TC-OPN-03"),
            pytest.param(CURRENT, "4999.99", "BELOW_OPENING_BALANCE", id="TC-OPN-04"),
            pytest.param(SAVINGS, "100000.00", "OK", id="TC-OPN-05"),
            pytest.param(SAVINGS, "100000.01", "INVALID_AMOUNT", id="TC-OPN-06"),
        ],
    )
    def test_opening_deposit_rules(self, bank, account_type, deposit, outcome):
        if outcome == "OK":
            assert open_account(bank, account_type, deposit).balance == money(deposit)
        else:
            assert_refused(ErrorCode[outcome], open_account, bank, account_type, deposit)

    def test_TC_OPN_07_sequential_ids_and_trimmed_name(self, bank):
        first = bank.open_account("  Thirth Patel ", SAVINGS, money("1000.00"))
        second = open_account(bank, CURRENT, "5000.00")
        assert (first.id, second.id) == ("ACC-0001", "ACC-0002")
        assert first.owner == "Thirth Patel"
        assert first.type is SAVINGS
        assert first.status is AccountStatus.ACTIVE

    def test_TC_OPN_08_refused_opening_has_no_effect(self, bank, notifier):
        assert_refused(ErrorCode.INVALID_OWNER_NAME, bank.open_account, "R2D2", SAVINGS, money("1000.00"))
        assert_refused(ErrorCode.ACCOUNT_NOT_FOUND, bank.get_account, "ACC-0001")
        notifier.send.assert_not_called()


class TestDepositing:
    def test_TC_DEP_01_adds_to_balance(self, bank):
        account = open_account(bank, SAVINGS, "1000.00")
        assert bank.deposit(account.id, money("250.50")) == money("1250.50")
        assert account.balance == money("1250.50")

    @pytest.mark.boundary
    @pytest.mark.parametrize(
        "amount",
        [pytest.param("0.99", id="TC-DEP-02"), pytest.param("100000.01", id="TC-DEP-03")],
    )
    def test_refuses_out_of_range_amount(self, bank, amount):
        account = open_account(bank, SAVINGS, "1000.00")
        assert_refused(ErrorCode.INVALID_AMOUNT, bank.deposit, account.id, money(amount))
        assert account.balance == money("1000.00")

    def test_TC_DEP_04_refuses_unknown_account(self, bank):
        assert_refused(ErrorCode.ACCOUNT_NOT_FOUND, bank.deposit, "ACC-9999", money("100.00"))

    def test_TC_DEP_05_allowed_when_frozen(self, bank):
        account = open_account(bank, SAVINGS, "1000.00")
        bank.freeze(account.id)
        bank.deposit(account.id, money("100.00"))
        assert account.balance == money("1100.00")

    def test_TC_DEP_06_refused_when_closed(self, bank):
        account = closed_account(bank)
        assert_refused(ErrorCode.ACCOUNT_CLOSED, bank.deposit, account.id, money("100.00"))


class TestWithdrawing:
    @pytest.mark.boundary
    @pytest.mark.parametrize("case", withdrawal_cases())
    def test_respects_balance_floor(self, bank, case):
        account = open_account(bank, AccountType[case["account_type"]], case["opening_deposit"])
        amount = money(case["withdrawal"])
        expected = money(case["expected_balance"])
        if case["expected_outcome"] == "OK":
            assert bank.withdraw(account.id, amount) == expected
        else:
            assert_refused(ErrorCode[case["expected_outcome"]], bank.withdraw, account.id, amount)
        assert account.balance == expected

    def test_TC_WD_09_refuses_invalid_amount(self, bank):
        account = open_account(bank, SAVINGS, "10000.00")
        assert_refused(ErrorCode.INVALID_AMOUNT, bank.withdraw, account.id, money("0.99"))

    def test_TC_WD_10_refuses_frozen(self, bank):
        account = open_account(bank, SAVINGS, "10000.00")
        bank.freeze(account.id)
        assert_refused(ErrorCode.ACCOUNT_FROZEN, bank.withdraw, account.id, money("100.00"))
        assert account.balance == money("10000.00")

    def test_TC_WD_11_refuses_closed(self, bank):
        account = closed_account(bank)
        assert_refused(ErrorCode.ACCOUNT_CLOSED, bank.withdraw, account.id, money("100.00"))


@pytest.mark.boundary
class TestDailyLimit:
    @pytest.fixture
    def rich(self, bank):
        account = open_account(bank, SAVINGS, "100000.00")
        bank.deposit(account.id, money("100000.00"))
        return account

    def test_TC_LIM_01_allows_exact_limit(self, bank, rich):
        bank.withdraw(rich.id, money("30000.00"))
        bank.withdraw(rich.id, money("20000.00"))
        assert rich.balance == money("150000.00")

    def test_TC_LIM_02_refuses_over_limit(self, bank, rich):
        bank.withdraw(rich.id, money("30000.00"))
        assert_refused(ErrorCode.DAILY_LIMIT_EXCEEDED, bank.withdraw, rich.id, money("20000.01"))
        assert rich.balance == money("170000.00")

    def test_TC_LIM_03_holds_until_midnight(self, bank, clock, rich):
        clock.advance(hours=13, minutes=59, seconds=59)
        bank.withdraw(rich.id, money("50000.00"))
        assert_refused(ErrorCode.DAILY_LIMIT_EXCEEDED, bank.withdraw, rich.id, money("1.00"))

    def test_TC_LIM_04_resets_at_midnight(self, bank, clock, rich):
        clock.advance(hours=13, minutes=59, seconds=59)
        bank.withdraw(rich.id, money("50000.00"))
        clock.advance(seconds=1)
        bank.withdraw(rich.id, money("50000.00"))
        assert rich.balance == money("100000.00")

    def test_TC_LIM_05_refused_withdrawal_not_counted(self, bank):
        small = open_account(bank, SAVINGS, "20000.00")
        assert_refused(ErrorCode.INSUFFICIENT_FUNDS, bank.withdraw, small.id, money("40000.00"))
        bank.deposit(small.id, money("100000.00"))
        bank.withdraw(small.id, money("50000.00"))
        assert small.balance == money("70000.00")

    def test_TC_LIM_06_limit_is_per_account(self, bank, rich):
        other = open_account(bank, SAVINGS, "60000.00")
        bank.withdraw(rich.id, money("50000.00"))
        bank.withdraw(other.id, money("50000.00"))
        assert other.balance == money("10000.00")


class TestTransferring:
    @pytest.fixture
    def sender(self, bank):
        return open_account(bank, SAVINGS, "20000.00")

    @pytest.fixture
    def receiver(self, bank):
        return open_account(bank, CURRENT, "5000.00")

    def test_TC_TRF_01_moves_money_without_fee(self, bank, sender, receiver):
        bank.transfer(sender.id, receiver.id, money("10000.00"))
        assert sender.balance == money("10000.00")
        assert receiver.balance == money("15000.00")
        assert tx_types(sender) == [TransactionType.OPENING_DEPOSIT, TransactionType.TRANSFER_OUT]

    def test_TC_TRF_02_charges_fee_to_sender_only(self, bank, sender, receiver):
        bank.transfer(sender.id, receiver.id, money("10000.01"))
        assert sender.balance == money("9994.99")
        assert receiver.balance == money("15000.01")
        assert tx_types(sender)[-2:] == [TransactionType.TRANSFER_OUT, TransactionType.TRANSFER_FEE]

    @pytest.mark.boundary
    @pytest.mark.parametrize(
        ("opening", "amount", "outcome", "expected"),
        [
            pytest.param("11000.00", "10000.00", "OK", "1000.00", id="TC-TRF-03"),
            pytest.param("11000.00", "10000.01", "INSUFFICIENT_FUNDS", "11000.00", id="TC-TRF-04"),
            pytest.param("11005.01", "10000.01", "OK", "1000.00", id="TC-TRF-05"),
            pytest.param("11005.00", "10000.01", "INSUFFICIENT_FUNDS", "11005.00", id="TC-TRF-06"),
        ],
    )
    def test_fee_is_part_of_funds_check(self, bank, receiver, opening, amount, outcome, expected):
        payer = open_account(bank, SAVINGS, opening)
        if outcome == "OK":
            bank.transfer(payer.id, receiver.id, money(amount))
        else:
            assert_refused(ErrorCode[outcome], bank.transfer, payer.id, receiver.id, money(amount))
        assert payer.balance == money(expected)

    @pytest.mark.boundary
    @pytest.mark.parametrize(
        ("amount", "outcome", "expected"),
        [
            pytest.param("14995.00", "OK", "-10000.00", id="TC-TRF-07"),
            pytest.param("14995.01", "INSUFFICIENT_FUNDS", "5000.00", id="TC-TRF-08"),
        ],
    )
    def test_current_account_can_use_overdraft(self, bank, sender, receiver, amount, outcome, expected):
        if outcome == "OK":
            bank.transfer(receiver.id, sender.id, money(amount))
        else:
            assert_refused(ErrorCode[outcome], bank.transfer, receiver.id, sender.id, money(amount))
        assert receiver.balance == money(expected)

    def test_TC_TRF_09_refuses_same_account(self, bank, sender):
        assert_refused(ErrorCode.SAME_ACCOUNT_TRANSFER, bank.transfer, sender.id, sender.id, money("100.00"))

    @pytest.mark.boundary
    @pytest.mark.parametrize(
        "amount",
        [pytest.param("0.99", id="TC-TRF-10"), pytest.param("100000.01", id="TC-TRF-11")],
    )
    def test_refuses_invalid_amount(self, bank, sender, receiver, amount):
        assert_refused(ErrorCode.INVALID_AMOUNT, bank.transfer, sender.id, receiver.id, money(amount))

    def test_TC_TRF_12_refuses_unknown_source(self, bank, receiver):
        assert_refused(ErrorCode.ACCOUNT_NOT_FOUND, bank.transfer, "ACC-9999", receiver.id, money("100.00"))

    def test_TC_TRF_13_unknown_destination_keeps_money(self, bank, sender):
        assert_refused(ErrorCode.ACCOUNT_NOT_FOUND, bank.transfer, sender.id, "ACC-9999", money("100.00"))
        assert sender.balance == money("20000.00")

    def test_TC_TRF_14_missing_source_id_is_not_found(self, bank, receiver):
        assert_refused(ErrorCode.ACCOUNT_NOT_FOUND, bank.transfer, None, receiver.id, money("100.00"))

    def test_TC_TRF_15_frozen_sender_refused(self, bank, sender, receiver):
        bank.freeze(sender.id)
        assert_refused(ErrorCode.ACCOUNT_FROZEN, bank.transfer, sender.id, receiver.id, money("100.00"))
        assert sender.balance == money("20000.00")

    def test_TC_TRF_16_frozen_receiver_allowed(self, bank, sender, receiver):
        bank.freeze(receiver.id)
        bank.transfer(sender.id, receiver.id, money("100.00"))
        assert receiver.balance == money("5100.00")

    @pytest.mark.atomicity
    def test_TC_TRF_17_closed_receiver_keeps_money_with_sender(self, bank, sender):
        closed = closed_account(bank)
        assert_refused(ErrorCode.ACCOUNT_CLOSED, bank.transfer, sender.id, closed.id, money("1000.00"))
        assert sender.balance == money("20000.00")
        assert tx_types(sender) == [TransactionType.OPENING_DEPOSIT]

    def test_TC_TRF_18_transfers_do_not_use_daily_limit(self, bank, receiver):
        rich = open_account(bank, SAVINGS, "100000.00")
        bank.transfer(rich.id, receiver.id, money("60000.00"))
        bank.withdraw(rich.id, money("30000.00"))
        assert rich.balance == money("9985.00")

    def test_TC_TRF_19_same_account_is_compared_by_value(self, bank, sender):
        equal_but_separate_id = "".join(list(sender.id))
        assert_refused(
            ErrorCode.SAME_ACCOUNT_TRANSFER, bank.transfer, sender.id, equal_but_separate_id, money("100.00")
        )


class TestInterest:
    def test_TC_MI_01_credits_savings(self, bank):
        account = open_account(bank, SAVINGS, "12000.00")
        assert bank.apply_monthly_interest(account.id) == money("30.00")
        assert account.balance == money("12030.00")
        assert account.transactions[-1].type is TransactionType.INTEREST

    def test_TC_MI_02_none_on_current(self, bank):
        account = open_account(bank, CURRENT, "12000.00")
        assert bank.apply_monthly_interest(account.id) == money("0.00")
        assert account.balance == money("12000.00")
        assert len(account.transactions) == 1

    def test_TC_MI_03_accrues_when_frozen(self, bank):
        account = open_account(bank, SAVINGS, "12000.00")
        bank.freeze(account.id)
        assert bank.apply_monthly_interest(account.id) == money("30.00")

    def test_TC_MI_04_refused_when_closed(self, bank):
        account = closed_account(bank)
        assert_refused(ErrorCode.ACCOUNT_CLOSED, bank.apply_monthly_interest, account.id)


class TestLifecycle:
    def test_TC_LIF_01_unfreeze_restores_withdrawals(self, bank):
        account = open_account(bank, SAVINGS, "10000.00")
        bank.freeze(account.id)
        bank.unfreeze(account.id)
        bank.withdraw(account.id, money("100.00"))
        assert account.balance == money("9900.00")

    def test_TC_LIF_02_cannot_freeze_twice(self, bank):
        account = open_account(bank, SAVINGS, "10000.00")
        bank.freeze(account.id)
        assert_refused(ErrorCode.ACCOUNT_FROZEN, bank.freeze, account.id)

    def test_TC_LIF_03_frozen_cannot_close(self, bank):
        account = open_account(bank, SAVINGS, "10000.00")
        bank.freeze(account.id)
        assert_refused(ErrorCode.ACCOUNT_FROZEN, bank.close, account.id)

    def test_TC_LIF_04_closed_is_final(self, bank):
        account = closed_account(bank)
        assert account.status is AccountStatus.CLOSED
        assert_refused(ErrorCode.ACCOUNT_CLOSED, bank.freeze, account.id)
        assert_refused(ErrorCode.ACCOUNT_CLOSED, bank.unfreeze, account.id)
        assert_refused(ErrorCode.ACCOUNT_CLOSED, bank.close, account.id)

    def test_TC_LIF_05_overdrawn_cannot_close(self, bank):
        account = open_account(bank, CURRENT, "5000.00")
        bank.withdraw(account.id, money("6000.00"))
        assert_refused(ErrorCode.OUTSTANDING_BALANCE, bank.close, account.id)
        assert account.status is AccountStatus.ACTIVE

    def test_TC_LIF_06_savings_can_be_closed_with_payout(self, bank):
        account = open_account(bank, SAVINGS, "1000.00")
        bank.close(account.id)
        assert account.status is AccountStatus.CLOSED
        assert account.balance == money("0.00")
        assert account.transactions[-1].type is TransactionType.CLOSING_PAYOUT
        assert account.transactions[-1].amount == money("1000.00")

    def test_TC_LIF_07_unknown_account_refused(self, bank):
        assert_refused(ErrorCode.ACCOUNT_NOT_FOUND, bank.get_account, "ACC-9999")

    @pytest.mark.boundary
    def test_TC_LIF_08_overdrawn_by_paise_cannot_close(self, bank):
        account = open_account(bank, CURRENT, "5000.00")
        bank.withdraw(account.id, money("5000.50"))
        assert_refused(ErrorCode.OUTSTANDING_BALANCE, bank.close, account.id)

    @pytest.mark.boundary
    def test_TC_LIF_09_balance_under_one_rupee_is_paid_out(self, bank):
        account = open_account(bank, CURRENT, "5000.00")
        bank.withdraw(account.id, money("4999.50"))
        bank.close(account.id)
        assert account.balance == money("0.00")
        assert account.transactions[-1].type is TransactionType.CLOSING_PAYOUT

    @pytest.mark.boundary
    def test_TC_LIF_10_zero_balance_close_adds_no_payout_line(self, bank):
        account = closed_account(bank)
        assert account.transactions[-1].type is TransactionType.WITHDRAWAL


class TestStatement:
    def test_TC_STM_01_records_amount_balance_and_time(self, bank, clock):
        account = open_account(bank, SAVINGS, "5000.00")
        clock.advance(hours=1)
        bank.withdraw(account.id, money("500.00"))
        assert account.transactions[-1] == Transaction(
            TransactionType.WITHDRAWAL, money("500.00"), money("4500.00"), clock.now
        )
        assert account.transactions[0].at == START

    def test_TC_STM_02_cannot_be_edited_from_outside(self, bank):
        account = open_account(bank, SAVINGS, "5000.00")
        assert isinstance(account.transactions, tuple)
        with pytest.raises(FrozenInstanceError):
            account.transactions[0].amount = money("1.00")


class TestNotifications:
    def test_TC_NOT_01_withdrawal_alerts_holder(self, bank, notifier):
        account = open_account(bank, SAVINGS, "5000.00")
        bank.withdraw(account.id, money("500.00"))
        notifier.send.assert_called_with(account.id, "Withdrew 500.00")

    def test_TC_NOT_02_transfer_alerts_both_sides_with_fee(self, bank, notifier):
        sender = open_account(bank, SAVINGS, "20000.00")
        receiver = open_account(bank, SAVINGS, "1000.00")
        notifier.send.reset_mock()
        bank.transfer(sender.id, receiver.id, money("10000.01"))
        assert [call.args for call in notifier.send.call_args_list] == [
            (sender.id, "Sent 10000.01 with fee 5.00"),
            (receiver.id, "Received 10000.01"),
        ]

    def test_TC_NOT_03_refused_withdrawal_is_silent(self, bank, notifier):
        account = open_account(bank, SAVINGS, "5000.00")
        notifier.send.reset_mock()
        assert_refused(ErrorCode.INSUFFICIENT_FUNDS, bank.withdraw, account.id, money("4000.01"))
        notifier.send.assert_not_called()

    def test_TC_NOT_04_outage_does_not_undo_withdrawal(self, bank, notifier, caplog):
        account = open_account(bank, SAVINGS, "5000.00")
        notifier.send.side_effect = ConnectionError("SMS gateway down")
        assert bank.withdraw(account.id, money("500.00")) == money("4500.00")
        assert account.balance == money("4500.00")
        assert "Notification failed" in caplog.text
        assert caplog.records[-1].exc_info is not None
        assert "SMS gateway down" in caplog.text

    def test_TC_NOT_05_deposit_and_interest_alert(self, bank, notifier):
        account = open_account(bank, SAVINGS, "12000.00")
        bank.deposit(account.id, money("100.00"))
        notifier.send.assert_called_with(account.id, "Deposited 100.00")
        bank.apply_monthly_interest(account.id)
        notifier.send.assert_called_with(account.id, ANY)
        assert "Interest credited" in notifier.send.call_args.args[1]


class TestRepository:
    def test_TC_REP_01_finds_saved_account(self, bank):
        repository = InMemoryAccountRepository()
        account = open_account(bank, SAVINGS, "1000.00")
        repository.save(account)
        assert repository.find_by_id(account.id) is account

    def test_TC_REP_02_empty_for_unknown_id(self):
        assert InMemoryAccountRepository().find_by_id("ACC-404") is None
