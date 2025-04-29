# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from rest.schema.balance import BalanceResponse
from rest.schema.credit_accounts import CreditAccount


@pytest.fixture
def account_id():
    return uuid4()


@pytest.fixture
def current_date():
    return datetime.now(tz=timezone.utc)


@pytest.fixture
def tomorrow_timestamp_in_milliseconds(current_date):
    tomorrow = current_date + timedelta(days=1)
    return int(tomorrow.timestamp() * 1000)


@pytest.fixture
def yesterday_timestamp_in_milliseconds(current_date):
    yesterday = current_date - timedelta(days=1)
    return int(yesterday.timestamp() * 1000)


@pytest.fixture
def creation_payload(tomorrow_timestamp_in_milliseconds):
    payload = {
        "name": "new credit account",
        "init_amount": 2000,
        "expires": tomorrow_timestamp_in_milliseconds,
    }
    return payload


@pytest.fixture
def creation_renewal_payload(creation_payload):
    creation_payload["renewable_amount"] = 2000
    creation_payload["renewal_day_of_month"] = 20

    return creation_payload


@pytest.fixture
def put_payload(tomorrow_timestamp_in_milliseconds):
    payload = {
        "name": "updated account name",
        "expires": tomorrow_timestamp_in_milliseconds,
    }
    return payload


@pytest.fixture
def put_renewal_payload(put_payload):
    put_payload["renewable_amount"] = 100

    return put_payload


@pytest.fixture
def balance_response():
    return BalanceResponse(
        incoming=100,
        available=100,
        blocked=0,
    )


@pytest.fixture
def credit_account(
    account_id,
    organization_id,
    yesterday_timestamp_in_milliseconds,
    tomorrow_timestamp_in_milliseconds,
    balance_response,
):
    return CreditAccount(
        id=account_id,
        organization_id=organization_id,
        name="account-name",
        created=yesterday_timestamp_in_milliseconds,
        updated=tomorrow_timestamp_in_milliseconds,
        balance=balance_response,
    )


@pytest.fixture
def renewal_credit_account(credit_account):
    renewal_credit_account = credit_account
    renewal_credit_account.renewable_amount = 200
    renewal_credit_account.renewal_day_of_month = 20

    return renewal_credit_account
