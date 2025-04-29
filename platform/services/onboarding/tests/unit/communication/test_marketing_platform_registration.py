# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


import os
from unittest import mock

import pytest

from communication.marketing_platform.register_user import register_user_in_marketing_platform


@pytest.mark.asyncio
@mock.patch.dict(
    os.environ,
    {
        "MARKETING_PLATFORM_URL": "example.com",
        "MARKETING_PLATFORM_FORM_NAME": "register",
        "MARKETING_PLATFORM_SITE_ID": "1234",
    },
)
async def test_register_user_in_marketing_platform(mocker):
    httpx_client_mock = mock.AsyncMock()
    async_client_mock = mocker.patch("communication.marketing_platform.register_user.httpx.AsyncClient")
    async_client_mock.return_value.__aenter__.return_value = httpx_client_mock
    test_user = mock.MagicMock(id_="1", first_name="foo", second_name="bar", email="foo@example.com", status=None)

    organization_name = "cheese"
    marketing_platform_address = "example.com"
    marketing_platform_form_name = "register"
    marketing_platform_site_id = "1234"
    country_code = "AU"
    profession = "pickle"

    await register_user_in_marketing_platform(
        user=test_user,
        organization_name=organization_name,
        country_code=country_code,
        profession=profession,
    )

    httpx_client_mock.post.assert_called_once_with(
        marketing_platform_address,
        data={
            "firstName": test_user.first_name,
            "lastName": test_user.second_name,
            "emailAddress": test_user.email,
            "organizationname": organization_name,
            "country": "Australia",
            "profession": profession,
            "elqFormName": marketing_platform_form_name,
            "elqSiteId": marketing_platform_site_id,
        },
    )


@pytest.mark.asyncio
@mock.patch.dict(
    os.environ,
    {
        "MARKETING_PLATFORM_URL": "example.com",
        "MARKETING_PLATFORM_FORM_NAME": "register",
        "MARKETING_PLATFORM_SITE_ID": "1234",
    },
)
async def test_register_user_in_marketing_platform_when_profession_empty(mocker):
    httpx_client_mock = mock.AsyncMock()
    async_client_mock = mocker.patch("communication.marketing_platform.register_user.httpx.AsyncClient")
    async_client_mock.return_value.__aenter__.return_value = httpx_client_mock
    test_user = mock.MagicMock(id_="1", first_name="foo", second_name="bar", email="foo@example.com", status=None)

    organization_name = "cheese"
    marketing_platform_address = "example.com"
    marketing_platform_form_name = "register"
    marketing_platform_site_id = "1234"
    country_code = "AU"
    profession = None

    await register_user_in_marketing_platform(
        user=test_user,
        organization_name=organization_name,
        country_code=country_code,
        profession=profession,
    )

    httpx_client_mock.post.assert_called_once_with(
        marketing_platform_address,
        data={
            "firstName": test_user.first_name,
            "lastName": test_user.second_name,
            "emailAddress": test_user.email,
            "organizationname": organization_name,
            "country": "Australia",
            "profession": "Not provided",
            "elqFormName": marketing_platform_form_name,
            "elqSiteId": marketing_platform_site_id,
        },
    )


@pytest.mark.asyncio
@mock.patch.dict(
    os.environ,
    {"MARKETING_PLATFORM_URL": "", "MARKETING_PLATFORM_FORM_NAME": "register", "MARKETING_PLATFORM_SITE_ID": "1234"},
)
async def test_register_user_in_marketing_platform_skip_when_not_configured(mocker):
    httpx_client_mock = mock.AsyncMock()
    async_client_mock = mocker.patch("communication.marketing_platform.register_user.httpx.AsyncClient")
    async_client_mock.return_value.__aenter__.return_value = httpx_client_mock
    test_user = mock.MagicMock(id_="1", first_name="foo", second_name="bar", email="foo@example.com", status=None)

    organization_name = "cheese"
    country_placeholder = "TEST"

    await register_user_in_marketing_platform(
        user=test_user,
        organization_name=organization_name,
        country_code=country_placeholder,
    )

    assert httpx_client_mock.post.call_count == 0
