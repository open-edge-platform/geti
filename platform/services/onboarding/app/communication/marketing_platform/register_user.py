# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from os import environ

import httpx
from iso3166 import countries

from geti_logger_tools.logger_config import initialize_logger
from models.user import User

logger = initialize_logger(__name__)

URL_ENV = "MARKETING_PLATFORM_URL"
FORM_NAME_ENV = "MARKETING_PLATFORM_FORM_NAME"
SITE_ID_ENV = "MARKETING_PLATFORM_SITE_ID"


def get_country_name(country_code: str) -> str:
    """
    Return country name given country code in ISO 3166-1 format.
    If no country is matched, return given country code.
    """
    country = countries.get(country_code, default=None)
    return country.name if country else country_code


async def register_user_in_marketing_platform(
    user: User,
    organization_name: str,
    profession: str | None = None,
    country_code: str | None = None,
) -> None:
    """
    Register user in Eloqua Marketing Platform.
    Marketing platform request is configured by MARKETING_PLATFORM_URL,
    MARKETING_PLATFORM_FORM_NAME, MARKETING_PLATFORM_SITE_ID environment variables.
    """

    platform_url = environ.get(URL_ENV)

    if not platform_url:
        logger.info(
            f"Marketing platform URL environment variable ({URL_ENV}) is not defined, "
            f"skipping registration in marketing platform."
        )
        return

    country_name = get_country_name(country_code) if country_code else "Unknown"
    profession_name = profession or "Not provided"

    registration_data = {
        "firstName": user.first_name,
        "lastName": user.second_name,
        "emailAddress": user.email,
        "organizationname": organization_name,
        "country": country_name,
        "profession": profession_name,
        "elqFormName": environ.get(FORM_NAME_ENV, ""),
        "elqSiteId": environ.get(SITE_ID_ENV, ""),
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(platform_url, data=registration_data)
        logger.info(
            f"Marketing platform response for user {user.first_name} {user.second_name} "
            f"in org {organization_name}: {response.status_code} {response.text}"
        )
        response.raise_for_status()
