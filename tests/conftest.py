"""Shared fixtures. Each test gets its own bank, clock and mocked notification gateway."""

import pytest
from hypothesis import settings

from bank.ports import NotificationGateway
from support import MutableClock, make_bank

# A fixed seed makes property-based runs repeatable, so they cannot be flaky between runs.
settings.register_profile("repeatable", derandomize=True, deadline=None)
settings.load_profile("repeatable")


@pytest.fixture
def clock():
    return MutableClock()


@pytest.fixture
def notifier(mocker):
    return mocker.create_autospec(NotificationGateway, instance=True)


@pytest.fixture
def bank(notifier, clock):
    return make_bank(notifier, clock)
