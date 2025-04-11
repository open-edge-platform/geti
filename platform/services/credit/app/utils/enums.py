# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from enum import Enum


class StrEnum(str, Enum):
    @classmethod
    def contains(cls, value: str) -> bool:
        return any(value == member for member in cls)


class ResourceUnit(StrEnum):
    """Billable Geti resource units"""

    IMAGE = "image"
    FRAME = "frame"


class CreditAccountType(StrEnum):
    """Available Geti credit account types"""

    ASSET = "ASSET"
    LEASE = "LEASE"
    SAAS = "SAAS"


class SubscriptionStatus(StrEnum):
    """Possible organization's subscription states"""

    NEW = "NEW"
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class AggregatesKey(StrEnum):
    """Allowed keys for transaction aggregates"""

    PROJECT = "project"
    SERVICE_NAME = "service_name"
    DATE = "date"


class CreditSystemTimeBoundaries(Enum):
    START = 1_711_929_600_000  # Date and time (GMT): Monday, April 1, 2024 12:00:00 AM
    END = 8_023_398_574_000  # Date and time (GMT): Friday, April 2, 2224 9:49:34 AM


class ServiceName(StrEnum):
    """Billable Geti services"""

    TRAINING = "training"
    OPTIMIZATION = "optimization"


class ExternalServiceName(StrEnum):
    """Names received from jobs microservice"""

    TRAIN = "train"


_service_name_mapping = {
    ExternalServiceName.TRAIN: ServiceName.TRAINING,
}


def map_service_name(external_value: str) -> str:
    """Maps service names received from jobs ms to credit system's service names"""
    try:
        external_enum = ExternalServiceName(external_value)
        internal_enum = _service_name_mapping[external_enum]
        return internal_enum.value
    except ValueError:
        raise ValueError(f"Invalid value received: {external_value}")
    except KeyError:
        raise ValueError(f"Unsupported enum value received: {external_enum}")


class QuotaType(StrEnum):
    """Names of the quotas' types for Geti microservices"""

    MAX_TRAINING_JOBS = "MAX_TRAINING_JOBS"
    MAX_USERS_COUNT = "MAX_USERS_COUNT"


class Tags(Enum):
    """Names of allowed tags in the application's endpoints."""

    CREDIT_ACCOUNTS = "Credit accounts"
    SUBSCRIPTIONS = "Subscriptions"
    TRANSACTIONS = "Transactions"
    PRODUCTS = "Products"
    INTERNAL = "Internal"
    BALANCE = "Balance"
    QUOTAS = "Quotas"
