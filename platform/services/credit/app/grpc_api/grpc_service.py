# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the gRPC server for the credit system microservice
"""

import logging
import os
from concurrent import futures
from typing import TYPE_CHECKING
from uuid import UUID

import grpc

from db.model import Subscription
from dependencies import get_session
from exceptions.custom_exceptions import (
    InsufficientBalanceException,
    InvalidStateTransitionException,
    SubscriptionExistsException,
)
from geti_telemetry_tools import unified_tracing
from grpc_interfaces.credit_system.pb.credit_system_service_pb2 import (
    CancelLeaseRequest,
    EmptyRequest,
    EmptyResponse,
    Error,
    ErrorCode,
    LeaseIdResponse,
    LeaseRequest,
    Product,
    ProductPolicy,
    ProductResponse,
    ProductsList,
    QuotaGetRequest,
    QuotaGetResponse,
    QuotaInfo,
    SubscriptionIdResponse,
    SubscriptionRequest,
)
from grpc_interfaces.credit_system.pb.credit_system_service_pb2_grpc import (
    LeaseServiceServicer,
    ProductServiceServicer,
    QuotaServiceServicer,
    SubscriptionServiceServicer,
    add_LeaseServiceServicer_to_server,
    add_ProductServiceServicer_to_server,
    add_QuotaServiceServicer_to_server,
    add_SubscriptionServiceServicer_to_server,
)
from service.product import ProductService
from service.subscription import SubscriptionService
from service.transaction import LeaseRequestData, TransactionService
from utils.enums import SubscriptionStatus, map_service_name
from utils.time import get_current_day

if TYPE_CHECKING:
    from rest.schema.subscription import SubscriptionQuota

logger = logging.getLogger(__name__)


class GrpcProductService(ProductServiceServicer):
    """
    This class implements ProductServiceServicer interface to handle
    getting credits products information via gRPC protocol.
    """

    @unified_tracing
    def get_all_products(self, request: EmptyRequest, context: grpc.ServicerContext) -> ProductResponse:  # noqa: ARG002
        """
        Get available SaaS credits products
        :return: list of products
        """
        logger.debug("Received gRPC get products request")
        try:
            with next(get_session()) as db_session:
                total, products = ProductService(db_session).get_all_products()
                logger.debug(f"Available products: {products}")
                proto_products = ProductsList(
                    products=[
                        Product(
                            id=str(prod.id),
                            name=prod.name,
                            created=prod.created,
                            updated=prod.updated,
                            product_policies=[
                                ProductPolicy(
                                    account_name=pol.account_name,
                                    init_amount=pol.init_amount,
                                    renewable_amount=pol.renewable_amount,
                                    expires_in=pol.expires_in,
                                )
                                for pol in prod.product_policies
                            ],
                        )
                        for prod in products
                    ]
                )
                return ProductResponse(products=proto_products)
        except Exception as exc:
            error_msg = "Failed to get available SaaS credits products"
            logger.exception(error_msg)
            context.abort(code=grpc.StatusCode.INTERNAL, details=error_msg)
            raise exc


class GrpcSubscriptionService(SubscriptionServiceServicer):
    """
    This class implements SubscriptionServiceServicer interface to handle
    organization's subscription creation via gRPC protocol.
    """

    @unified_tracing
    def activate(self, request: SubscriptionRequest, context: grpc.ServicerContext) -> SubscriptionIdResponse:
        """
        Creates a product subscription.

        :param request: the SubscriptionCreateRequest containing the data for the new subscription
        :param context: the gRPC context for the request
        :return: SubscriptionIdResponse containing the id of the created subscription
        """
        logger.debug(f"Received create subscription request for the organization: {request.organization_id}")
        try:
            with next(get_session()) as db_session:
                subscription_service = SubscriptionService(db_session)
                existing_subscription: Subscription | None = subscription_service.get_product_subscription(
                    organization_id=request.organization_id, product_id=UUID(request.product_id)
                )
                if existing_subscription is not None and existing_subscription.status == SubscriptionStatus.ACTIVE:
                    return SubscriptionIdResponse(id=str(existing_subscription.id))

                subscription_data = (
                    existing_subscription
                    if existing_subscription is not None and existing_subscription.status == SubscriptionStatus.FAILED
                    else Subscription(
                        organization_id=request.organization_id,
                        workspace_id=request.workspace_id,
                        product_id=UUID(request.product_id),
                        renewal_day_of_month=get_current_day(),
                        status=SubscriptionStatus.NEW,
                    )
                )
                result_subscription = subscription_service.transition(
                    subscription=subscription_data,
                    new_status=SubscriptionStatus.ACTIVE,
                    organization_id=request.organization_id,
                    _db_session=db_session,
                )
                return SubscriptionIdResponse(id=str(result_subscription.id))

        except SubscriptionExistsException:
            return SubscriptionIdResponse(
                error=Error(
                    code=ErrorCode.SUBSCRIPTION_ALREADY_EXISTS,
                    message=(
                        f"Organization {request.organization_id} is already subscribed "
                        f"to SaaS credits product {request.product_id}"
                    ),
                )
            )
        except Exception as exc:
            error_msg = (
                f"Failed to subscribe organization {request.organization_id} to SaaS credits product "
                f"{request.product_id}"
            )
            logger.exception(error_msg)
            context.abort(code=grpc.StatusCode.INTERNAL, details=error_msg)
            raise exc

    @unified_tracing
    def find_active_subscription(
        self, request: SubscriptionRequest, context: grpc.ServicerContext
    ) -> SubscriptionIdResponse:
        """
        Looks for existing organization's subscription for the provided product_id in active state.

        :param request: gRPC message containing the organization and product ids for the subscription lookup
        :param context: the gRPC context for the request
        :return: SubscriptionIdResponse containing credits subscription ID or None, if there's no subscription found
        """
        try:
            with next(get_session()) as db_session:
                subscription_service = SubscriptionService(db_session)
                subscription: Subscription | None = subscription_service.get_active_product_subscription(
                    organization_id=request.organization_id, product_id=UUID(request.product_id)
                )
                if subscription:
                    logger.info(
                        f"Organization {request.organization_id} is currently subscribed to the product"
                        f" {request.product_id}, subscription id: {subscription.id}."
                    )
                    return SubscriptionIdResponse(id=str(subscription.id))
                message = (
                    f"Organization {request.organization_id} is not subscribed to the product {request.product_id}."
                )
                logger.info(message)
                return SubscriptionIdResponse(error=Error(code=ErrorCode.SUBSCRIPTION_NOT_FOUND, message=message))

        except Exception as exc:
            error_msg = (
                f"Failed to find organization {request.organization_id} subscription to SaaS credits product "
                f"{request.product_id}."
            )
            logger.exception(error_msg)
            context.abort(code=grpc.StatusCode.INTERNAL, details=error_msg)
            raise exc

    @unified_tracing
    def fail_subscription(self, request: SubscriptionRequest, context: grpc.ServicerContext) -> SubscriptionIdResponse:
        """Marks subscription's status as failed

        :param request: gRPC message containing the organization and product ids for the subscription lookup
        :param context: the gRPC context for the request
        :return: SubscriptionIdResponse containing credits subscription ID or None, if there's no subscription found
        """
        try:
            with next(get_session()) as db_session:
                subscription_service = SubscriptionService(db_session)
                subscription: Subscription | None = subscription_service.get_active_product_subscription(
                    organization_id=request.organization_id, product_id=UUID(request.product_id)
                )
                if subscription:
                    subscription_service.transition(
                        subscription=subscription,
                        new_status=SubscriptionStatus.FAILED,
                        organization_id=request.organization_id,
                        _db_session=db_session,
                    )
                    return SubscriptionIdResponse(id=str(subscription.id))
                message = (
                    f"Organization {request.organization_id} is not subscribed to the product {request.product_id}."
                )
                logger.info(message)
                return SubscriptionIdResponse(error=Error(code=ErrorCode.SUBSCRIPTION_NOT_FOUND, message=message))
        except InvalidStateTransitionException as exc:
            error_message = "Cannot change subscription status to failed."
            context.abort(code=grpc.StatusCode.INVALID_ARGUMENT, details=error_message)
            raise exc
        except Exception as exc:
            logger.exception(exc, exc_info=True)
            error_message = "Unexpected error during subscription rollback."
            context.abort(code=grpc.StatusCode.INTERNAL, details=error_message)
            raise exc


class GrpcLeaseService(LeaseServiceServicer):
    """
    This class implements LeaseServiceServicer interface to handle
    lease acquisitions and cancellations via gRPC protocol.
    """

    @unified_tracing
    def acquire(self, request: LeaseRequest, context) -> LeaseIdResponse:  # noqa: ANN001
        """
        Creates a lease transaction.

        :param request: the LeaseRequest containing the data for new lease transaction
        :param context: the gRPC context for the request
        :return: LeaseIdResponse containing the id of the acquired lease
        """
        logger.info(
            f"Received lease acquire request for the organization {request.organization_id}, "
            f"project id {request.project_id}, resources: {request.requests}."
        )
        try:
            with next(get_session()) as session:
                active_subscription = SubscriptionService(session=session).get_active_subscription(
                    organization_id=request.organization_id
                )
                if not active_subscription:
                    return LeaseIdResponse(
                        error=Error(
                            code=ErrorCode.SUBSCRIPTION_NOT_FOUND,
                            message=f"Cannot create a lease: organization {request.organization_id} "
                            f"has no active subscriptions.",
                        )
                    )
                service_name = map_service_name(external_value=request.service_name)
                lease_requests_data = {request.unit: request.amount for request in request.requests}
                request_data = LeaseRequestData(
                    service_name=service_name,
                    requests=lease_requests_data,
                    project_id=request.project_id,
                )
                transaction_service = TransactionService(session=session)

                tx_group_id = transaction_service.acquire_lease(
                    details=request_data,
                    subscription=active_subscription,
                    organization_id=request.organization_id,
                    _db_session=session,
                )
                return LeaseIdResponse(id=tx_group_id)
        except InsufficientBalanceException as balance_msg:
            return LeaseIdResponse(error=Error(code=ErrorCode.INSUFFICIENT_BALANCE, message=str(balance_msg)))
        except Exception as exc:
            error_msg = f"Failed to acquire lease for the organization {request.organization_id} due to internal error."
            logger.exception(error_msg)
            context.abort(code=grpc.StatusCode.INTERNAL, details=error_msg)
            raise exc

    @unified_tracing
    def cancel(self, request: CancelLeaseRequest, context) -> EmptyResponse:  # noqa: ANN001
        """
        Reverts the lease transaction.

        :param request: the CancelLeaseRequest containing the lease ID
        :param context: the gRPC context for the request
        :return: EmptyResponse
        """
        with next(get_session()) as session:
            transaction_service = TransactionService(session=session)
            try:
                transaction_service.cancel_lease(lease_id=request.id, _db_session=session)
            except Exception:
                error_msg = f"Failed to cancel lease with id {request.id} due to internal error."
                logger.exception(error_msg)
                context.abort(code=grpc.StatusCode.INTERNAL, details=error_msg)
        return EmptyResponse()


class GrpcQuotaService(QuotaServiceServicer):
    """
    This class implements QuotaServiceServicer interface to handle
    subscription quotas retrieval via gRPC protocol.
    """

    def get(self, request: QuotaGetRequest, context: grpc.ServicerContext) -> QuotaGetResponse:
        logger.debug(
            f"Received get quota request for the organization {request.organization_id}, requested quota type:"
            f" {request.quota_type}"
        )
        try:
            with next(get_session()) as db_session:
                subscription_service = SubscriptionService(db_session)
                quota: SubscriptionQuota | None = subscription_service.get_org_quota_by_type(
                    organization_id=request.organization_id, quota_type=request.quota_type
                )
                if not quota:
                    return QuotaGetResponse(
                        error=Error(
                            code=ErrorCode.INVALID_ARGUMENT,
                            message=(
                                f"Organization {request.organization_id} doesn't have a quota of type "
                                f"{request.quota_type}"
                            ),
                        )
                    )
                return QuotaGetResponse(
                    quota_info=QuotaInfo(
                        organization_id=quota.organization_id,
                        service_name=quota.service_name,
                        quota_type=quota.quota_type,
                        quota_name=quota.quota_name,
                        limit=quota.limit,
                        id=str(quota.id) if quota.id else None,
                    )
                )
        except Exception as exc:
            error_msg = f"Failed to get quotas information for the organization {request.organization_id}"
            logger.exception(error_msg)
            context.abort(code=grpc.StatusCode.INTERNAL, details=error_msg)
            raise exc


def run_grpc_server() -> None:
    """
    Starts the server and listens for requests.
    """
    grpc_port = os.environ.get("GRPC_SERVICE_PORT", "5556")
    address = f"[::]:{grpc_port}"
    logger.info(f"gRPC server version 0.1 on port {address}")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_LeaseServiceServicer_to_server(GrpcLeaseService(), server)
    add_ProductServiceServicer_to_server(GrpcProductService(), server)
    add_SubscriptionServiceServicer_to_server(GrpcSubscriptionService(), server)
    add_QuotaServiceServicer_to_server(GrpcQuotaService(), server)
    server.add_insecure_port(address)
    server.start()
    server.wait_for_termination()
