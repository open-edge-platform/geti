# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import json
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

import grpc

from .pb.credit_system_service_pb2 import (
    CancelLeaseRequest,
    EmptyRequest,
    ErrorCode,
    LeaseIdResponse,
    LeaseRequest,
    ProductResponse,
    ProductsList,
    QuotaGetRequest,
    QuotaGetResponse,
    QuotaInfo,
    SubscriptionIdResponse,
    SubscriptionRequest,
)
from .pb.credit_system_service_pb2_grpc import (
    LeaseServiceStub,
    ProductServiceStub,
    QuotaServiceStub,
    SubscriptionServiceStub,
)

logger = logging.getLogger(__name__)

# Telemetry is an optional yet recommended dependency for this gRPC client
try:
    from geti_telemetry_tools import ENABLE_TRACING, GrpcClientTelemetry

    if ENABLE_TRACING:
        GrpcClientTelemetry.instrument()
        logger.info("gRPC client instrumented for tracing")
    else:
        logger.info("gRPC client NOT instrumented for tracing (ENABLE_TRACING is false)")
except (ModuleNotFoundError, ImportError):
    logger.warning("gRPC client NOT instrumented for tracing (missing telemetry package)")

CREDITS_SERVICE = os.getenv("CREDITS_SERVICE", "localhost:5556")
GRPC_MAX_MESSAGE_SIZE = int(os.environ.get("GRPC_MAX_MESSAGE_SIZE", 128 * 1024**2))  # noqa: PLW1508


class InsufficientCreditsException(Exception):
    """
    Exception raised when organization doesn't have sufficient credits for acquiring a lease.
    """

    def __init__(self) -> None:
        super().__init__("Not enough credits for lease acquiring")


class SupportedServiceName(str, Enum):
    TRAIN = "train"

    @classmethod
    def contains(cls, value: str) -> bool:
        return any(value == member for member in cls)


class QuotaType(str, Enum):
    MAX_TRAINING_JOBS = "MAX_TRAINING_JOBS"
    MAX_USERS_COUNT = "MAX_USERS_COUNT"


@dataclass
class ResourceRequest:
    amount: int
    unit: str


class CreditSystemClient:
    """
    Client to interact with the credit system service via gRPC.

    :param metadata_getter: Lazy-evaluated function that returns the metadata to include
        in the gRPC request. It is typically used to propagate the session context.
        If the function returns None, then no metadata is propagated.
    """

    RETRY_MAX_ATTEMPTS = 5
    RETRY_INITIAL_BACKOFF = 1
    RETRY_MAX_BACKOFF = 4
    RETRY_BACKOFF_MULTIPLIER = 2

    def __init__(self, metadata_getter: Callable[[], tuple[tuple[str, str], ...] | None]) -> None:
        self.metadata_getter = metadata_getter
        self.grpc_channel = grpc.insecure_channel(
            CREDITS_SERVICE,
            options=[
                (
                    "grpc.service_config",
                    json.dumps(
                        {
                            "methodConfig": [
                                {
                                    "name": [{}],  # to match all RPCs from the credit system
                                    "retryPolicy": {
                                        "maxAttempts": self.RETRY_MAX_ATTEMPTS,
                                        "initialBackoff": f"{self.RETRY_INITIAL_BACKOFF}s",
                                        "maxBackoff": f"{self.RETRY_MAX_BACKOFF}s",
                                        "backoffMultiplier": self.RETRY_BACKOFF_MULTIPLIER,
                                        "retryableStatusCodes": ["UNAVAILABLE"],
                                    },
                                }
                            ]
                        }
                    ),
                ),
                ("grpc.max_send_message_length", GRPC_MAX_MESSAGE_SIZE),
                ("grpc.max_receive_message_length", GRPC_MAX_MESSAGE_SIZE),
            ],
        )
        self.products_service_stub = ProductServiceStub(self.grpc_channel)
        self.subscription_service_stub = SubscriptionServiceStub(self.grpc_channel)
        self.lease_service_stub = LeaseServiceStub(self.grpc_channel)
        self.quotas_service_stub = QuotaServiceStub(self.grpc_channel)

    def get_all_products(self) -> ProductsList:
        """
        Get available SaaS credits products

        :return: list of products
        """
        logger.info("Trying to get available SaaS credits products...")
        try:
            response: ProductResponse = self.products_service_stub.get_all_products(
                request=EmptyRequest(), metadata=self.metadata_getter()
            )
            match response.WhichOneof("result"):
                case "products":
                    logger.info(f"Available SaaS credits products: {response.products}")
                    return response.products
                case "error":
                    logger.error(f"{response.error.message}, error code: {response.error.code}")
                case _:
                    logger.error(
                        "Failed to get available SaaS credits products: invalid response from the gRPC service."
                    )
            raise RuntimeError("Failed to get available SaaS credits products.")
        except grpc.RpcError as e:
            logger.exception(
                f"ProductsRequest failed with error '{e.code().name}', message: '{e.details()}', "
                f"details: {e.trailing_metadata()}"
            )
            raise

    def create_subscription(
        self,
        organization_id: str,
        workspace_id: str,
        product_id: str,
    ) -> str | None:
        """
        Create an organization's subscription for a certain product

        :param organization_id: organization ID
        :param workspace_id: workspace ID
        :param product_id: SaaS credits product ID
        :return str: credits subscription ID
        """
        logger.info(
            f"Trying to create a subscription for organization {organization_id}, "
            f"chosen credits product id: {product_id}."
        )
        request = SubscriptionRequest(
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_id=product_id,
        )
        try:
            response: SubscriptionIdResponse = self.subscription_service_stub.activate(
                request, metadata=self.metadata_getter()
            )
            match response.WhichOneof("result"):
                case "id":
                    logger.info(
                        f"Subscription to the product with id {product_id} for organization {organization_id} "
                        f"has been successfully created."
                    )
                    return response.id
                case "error":
                    if response.error.code == ErrorCode.SUBSCRIPTION_ALREADY_EXISTS:
                        # the organization is already subscribed, no further action needed
                        logger.error(response.error.message)
                        return None

                    raise RuntimeError(
                        f"Request failed with error code {response.error.code}, "
                        f"error message: '{response.error.message}'"
                    )
                case _:
                    raise RuntimeError(
                        f"Failed to subscribe organization {organization_id} to the product {product_id}: "
                        f"invalid response from the gRPC service."
                    )
        except grpc.RpcError as e:
            logger.exception(
                f"Create subscription request failed with error '{e.code().name}', message: '{e.details()}', "
                f"details: {e.trailing_metadata()}"
            )
            raise

    def fail_subscription(self, organization_id: str, workspace_id: str, product_id: str) -> str | None:
        """Moves specified subscription to a failed state"""
        logger.info(
            f"Trying to update organization {organization_id} active subscription's state to 'failed', "
            f"credits product id: {product_id}."
        )
        request = SubscriptionRequest(
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_id=product_id,
        )
        try:
            response: SubscriptionIdResponse = self.subscription_service_stub.fail_subscription(
                request, metadata=self.metadata_getter()
            )
            match response.WhichOneof("result"):
                case "id":
                    logger.info(
                        f"Subscription to the product with id {product_id} for organization {organization_id} "
                        f"has been updated to failed status."
                    )
                    return response.id
                case "error":
                    if response.error.code == ErrorCode.INVALID_ARGUMENT:
                        raise ValueError("Cannot transition subscription to failed state from its current status.")

                    if response.error.code == ErrorCode.SUBSCRIPTION_NOT_FOUND:
                        logger.info("Subscription wasn't activated, skipping.")
                        return None

                    raise RuntimeError(
                        f"Request failed with error code {response.error.code}, "
                        f"error message: '{response.error.message}'"
                    )
                case _:
                    raise RuntimeError(
                        f"Request failed with error code {response.error.code}, "
                        f"error message: '{response.error.message}'"
                    )
        except grpc.RpcError as e:
            logger.exception(
                f"Fail subscription request failed with error '{e.code().name}', message: '{e.details()}', "
                f"details: {e.trailing_metadata()}"
            )
            raise

    def find_active_subscription(self, organization_id: str, workspace_id: str, product_id: str) -> str | None:
        """
        Find existing organization's subscription for the provided product_id in active state

        :param organization_id: organization ID
        :param workspace_id: workspace ID
        :param product_id: SaaS credits product ID
        :return: credits subscription ID or None, if there's no subscription found
        """
        request = SubscriptionRequest(organization_id=organization_id, workspace_id=workspace_id, product_id=product_id)
        try:
            response: SubscriptionIdResponse = self.subscription_service_stub.find_active_subscription(
                request, metadata=self.metadata_getter()
            )
            match response.WhichOneof("result"):
                case "id":
                    logger.info(
                        f"Organization {organization_id} is subscribed to the product with id {product_id}."
                        f" Subscription id: {response.id}."
                    )
                    return response.id
                case "error":
                    if response.error.code == ErrorCode.SUBSCRIPTION_NOT_FOUND:
                        logger.info(f"Organization {organization_id} is not subscribed to the product {product_id}.")
                        return None

                    raise RuntimeError(
                        f"Request failed with error code {response.error.code}, "
                        f"error message: '{response.error.message}'"
                    )
                case _:
                    raise RuntimeError(
                        f"Failed to find organization {organization_id} subscription to the product {product_id}: "
                        f"invalid response from the gRPC service."
                    )
        except grpc.RpcError as e:
            logger.exception(
                f"Find active subscription request failed with error '{e.code().name}', message: '{e.details()}', "
                f"details: {e.trailing_metadata()}"
            )
            raise

    def acquire_lease(
        self,
        organization_id: str,
        workspace_id: str,
        service_name: str,
        requests: list[ResourceRequest],
        project_id: str | None = None,
    ) -> str:
        """
        Acquire a credits lease for paid resources consumption

        :param organization_id: organization ID
        :param workspace_id: workspace ID
        :param project_id: project ID, optional
        :param service_name: name of the service which plans to consume paid resources
        :param requests: a list of dicts, which specify paid resource units and their corresponding amounts
        :raises UserDoesNotExist: On failure to find a user with the provided UID.
        :return str: credits lease ID
        """
        logger.debug(
            f"Organization {organization_id} is trying to acquire {requests} credits lease for project "
            f"{project_id}, service type {service_name}"
        )

        resource_requests = [LeaseRequest.ResourceRequest(unit=req.unit, amount=req.amount) for req in requests]

        if not SupportedServiceName.contains(service_name):
            raise ValueError(
                f"Supported service names: {[item.value for item in SupportedServiceName]}, received: {service_name}."
            )

        request = LeaseRequest(
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            service_name=service_name,
            requests=resource_requests,
        )
        try:
            response: LeaseIdResponse = self.lease_service_stub.acquire(request, metadata=self.metadata_getter())
            match response.WhichOneof("result"):
                case "id":
                    logger.info(
                        f"Credits lease has been successfully acquired for project {project_id}, "
                        f"service type {service_name}"
                    )
                    return response.id
                case "error":
                    if response.error.code in {ErrorCode.INSUFFICIENT_BALANCE, ErrorCode.SUBSCRIPTION_NOT_FOUND}:
                        logger.error(
                            f"Failed to acquire credits lease for project {project_id}, service type {service_name}. "
                            f"{response.error.message}"
                        )
                        raise InsufficientCreditsException

                    raise RuntimeError(
                        f"Request failed with error code {response.error.code}, "
                        f"error message: '{response.error.message}'"
                    )
                case _:
                    logger.error(
                        f"Failed to acquire credits lease for project {project_id}, service type {service_name}: "
                        f"invalid response from the gRPC service."
                    )
                    raise ValueError("Unknown service response")
        except grpc.RpcError as e:
            logger.exception(
                f"LeaseRequest failed with error '{e.code().name}', message: '{e.details()}', "
                f"details: {e.trailing_metadata()}"
            )
            raise

    def cancel_lease(self, lease_id: str) -> None:
        """
        Cancels credits lease

        :param lease_id: credits lease ID
        """
        logger.debug(f"Trying to cancel lease {lease_id}")
        request = CancelLeaseRequest(id=lease_id)
        try:
            self.lease_service_stub.cancel(request, metadata=self.metadata_getter())
            logger.info(f"Credits lease {lease_id} has been successfully cancelled")
        except grpc.RpcError as e:
            logger.exception(f"CancelLeaseRequest failed with error '{e.code().name}', message: '{e.details()}'")
            raise

    def get_users_quota(self, organization_id: str) -> int:
        """
        Returns the maximum allowed number of users for the organization
        or raises an exception if no such quota is set.
        """
        quota: QuotaInfo = self._get_quota(organization_id=organization_id, quota_type=QuotaType.MAX_USERS_COUNT)
        return quota.limit

    def get_jobs_quota(self, organization_id: str) -> int:
        """
        Returns the maximum allowed number of training jobs for the organization
        or raises an exception if no such quota is set.
        """
        quota: QuotaInfo = self._get_quota(organization_id=organization_id, quota_type=QuotaType.MAX_TRAINING_JOBS)
        return quota.limit

    def _get_quota(self, organization_id: str, quota_type: QuotaType) -> QuotaInfo:
        """Returns the quota of the requested type or raises an exception if no such quota exists"""
        request = QuotaGetRequest(organization_id=organization_id, quota_type=quota_type)
        try:
            response: QuotaGetResponse = self.quotas_service_stub.get(request, metadata=self.metadata_getter())
            match response.WhichOneof("result"):
                case "quota_info":
                    quota = response.quota_info
                    logger.debug(
                        f"Received quota for the organization {quota.organization_id}, service {quota.service_name}, "
                        f"quota type {quota.quota_type}: the limit is {quota.limit}."
                    )
                    return quota
                case "error":
                    raise RuntimeError(
                        f"Invalid request. Error code {response.error.code}, error message: '{response.error.message}'"
                    )
                case _:
                    raise RuntimeError(
                        f"Failed to get quotas information for the organization {organization_id}: "
                        f"invalid response from the gRPC service."
                    )
        except grpc.RpcError as e:
            logger.exception(
                f"Failed to get quotas information for the organization {organization_id}: error '{e.code().name}', "
                f"message: '{e.details()}', details: {e.trailing_metadata()}"
            )
            raise

    def close(self) -> None:
        """Close the GRPC channel."""
        logger.info("Closing GRPC channel at address `%s`.", CREDITS_SERVICE)
        self.grpc_channel.close()

    def __enter__(self) -> "CreditSystemClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        self.close()
