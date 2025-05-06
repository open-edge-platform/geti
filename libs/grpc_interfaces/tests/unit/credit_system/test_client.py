# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import MagicMock, patch

import grpc
import pytest
from grpc._channel import _InactiveRpcError, _RPCState

from grpc_interfaces.credit_system.client import (
    CreditSystemClient,
    InsufficientCreditsException,
    QuotaType,
    ResourceRequest,
)
from grpc_interfaces.credit_system.pb.credit_system_service_pb2 import (
    CancelLeaseRequest,
    EmptyResponse,
    Error,
    ErrorCode,
    LeaseIdResponse,
    LeaseRequest,
    Product,
    ProductPolicy,
    ProductResponse,
    ProductsList,
    QuotaGetResponse,
    QuotaInfo,
    SubscriptionIdResponse,
    SubscriptionRequest,
)


@pytest.fixture
def fxt_grpc_client():
    client = CreditSystemClient(metadata_getter=lambda: (("key", "value"),))
    client.lease_service_stub = MagicMock()
    client.subscription_service_stub = MagicMock()
    client.products_service_stub = MagicMock()
    yield client


class TestCreditSystemServiceClient:
    def test_acquire_lease_no_project_info(self, fxt_grpc_client) -> None:
        # Arrange
        response = LeaseIdResponse(id="lease_id")
        expected_grpc_message = LeaseRequest(
            organization_id="organization_id",
            workspace_id="workspace_id",
            service_name="train",
            requests=[LeaseRequest.ResourceRequest(amount=100, unit="image")],
        )
        with patch.object(fxt_grpc_client.lease_service_stub, "acquire", return_value=response) as mocked_acquire:
            # Act
            request = ResourceRequest(unit="image", amount=100)
            fxt_grpc_client.acquire_lease(
                organization_id="organization_id",
                workspace_id="workspace_id",
                service_name="train",
                requests=[request],
            )

        # Assert
        mocked_acquire.assert_called_once_with(expected_grpc_message, metadata=(("key", "value"),))

    def test_acquire_lease(self, fxt_grpc_client) -> None:
        # Arrange
        response = LeaseIdResponse(id="lease_id")
        expected_grpc_message = LeaseRequest(
            organization_id="organization_id",
            workspace_id="workspace_id",
            project_id="project_id",
            service_name="train",
            requests=[LeaseRequest.ResourceRequest(amount=100, unit="image")],
        )
        with patch.object(fxt_grpc_client.lease_service_stub, "acquire", return_value=response) as mocked_acquire:
            # Act
            request = ResourceRequest(unit="image", amount=100)
            fxt_grpc_client.acquire_lease(
                organization_id="organization_id",
                workspace_id="workspace_id",
                project_id="project_id",
                service_name="train",
                requests=[request],
            )

        # Assert
        mocked_acquire.assert_called_once_with(expected_grpc_message, metadata=(("key", "value"),))

    def test_acquire_lease_insufficient_credits(self, fxt_grpc_client) -> None:
        # Arrange
        response = LeaseIdResponse(error=Error(code=ErrorCode.INSUFFICIENT_BALANCE, message="Insufficient balance"))
        expected_grpc_message = LeaseRequest(
            organization_id="organization_id",
            workspace_id="workspace_id",
            project_id="project_id",
            service_name="train",
            requests=[LeaseRequest.ResourceRequest(amount=100, unit="image")],
        )
        with (
            patch.object(fxt_grpc_client.lease_service_stub, "acquire", return_value=response) as mocked_acquire,
            pytest.raises(InsufficientCreditsException),
        ):
            # Act
            request = ResourceRequest(unit="image", amount=100)
            fxt_grpc_client.acquire_lease(
                organization_id="organization_id",
                workspace_id="workspace_id",
                project_id="project_id",
                service_name="train",
                requests=[request],
            )

        # Assert
        mocked_acquire.assert_called_once_with(expected_grpc_message, metadata=(("key", "value"),))

    def test_acquire_lease_unsupported_service_name(self, fxt_grpc_client) -> None:
        with patch.object(fxt_grpc_client.lease_service_stub, "acquire") as mocked_acquire, pytest.raises(ValueError):
            # Act
            request = ResourceRequest(unit="image", amount=100)
            fxt_grpc_client.acquire_lease(
                organization_id="organization_id",
                workspace_id="workspace_id",
                project_id="project_id",
                service_name="unsupported-service-name",
                requests=[request],
            )
        # Assert
        mocked_acquire.assert_not_called()

    def test_cancel_lease(self, fxt_grpc_client) -> None:
        # Arrange
        response = EmptyResponse()
        expected_grpc_message = CancelLeaseRequest(id="lease_id")
        with patch.object(fxt_grpc_client.lease_service_stub, "cancel", return_value=response) as mocked_cancel:
            # Act
            fxt_grpc_client.cancel_lease(lease_id="lease_id")

        # Assert
        mocked_cancel.assert_called_once_with(expected_grpc_message, metadata=(("key", "value"),))

    def test_create_subscription_success(self, fxt_grpc_client) -> None:
        # Arrange
        expected_response = SubscriptionIdResponse(id="subscription_id_123")
        expected_request = SubscriptionRequest(
            organization_id="organization_id",
            workspace_id="workspace_id",
            product_id="product_id_123",
        )
        with patch.object(
            fxt_grpc_client.subscription_service_stub, "activate", return_value=expected_response
        ) as mocked_create_subscription:
            # Act
            result = fxt_grpc_client.create_subscription(
                organization_id="organization_id",
                workspace_id="workspace_id",
                product_id="product_id_123",
            )
        # Assert
        mocked_create_subscription.assert_called_once_with(expected_request, metadata=(("key", "value"),))
        assert result == expected_response.id

    def test_create_subscription_failure(self, fxt_grpc_client) -> None:
        # Arrange
        expected_request = SubscriptionRequest(
            organization_id="organization_id",
            workspace_id="workspace_id",
            product_id="product_id_123",
        )
        with (
            patch.object(
                fxt_grpc_client.subscription_service_stub,
                "activate",
                side_effect=_InactiveRpcError(
                    state=_RPCState(
                        code=grpc.StatusCode.INTERNAL,
                        details="Test error details",
                        trailing_metadata=None,
                        initial_metadata=None,
                        due=[],
                    )
                ),
            ) as mocked_create_subscription,
            pytest.raises(grpc.RpcError, match="Test error details"),
        ):
            # Act
            fxt_grpc_client.create_subscription(
                organization_id="organization_id",
                workspace_id="workspace_id",
                product_id="product_id_123",
            )
        # Assert
        mocked_create_subscription.assert_called_once_with(expected_request, metadata=(("key", "value"),))

    def test_create_subscription_already_exists(self, fxt_grpc_client) -> None:
        # Arrange
        grpc_response = SubscriptionIdResponse(
            error=Error(code=ErrorCode.SUBSCRIPTION_ALREADY_EXISTS, message="Subscription already exists")
        )
        expected_result = None
        expected_request = SubscriptionRequest(
            organization_id="organization_id",
            workspace_id="workspace_id",
            product_id="product_id_123",
        )
        with patch.object(
            fxt_grpc_client.subscription_service_stub, "activate", return_value=grpc_response
        ) as mocked_create_subscription:
            # Act
            result = fxt_grpc_client.create_subscription(
                organization_id="organization_id",
                workspace_id="workspace_id",
                product_id="product_id_123",
            )
        # Assert
        mocked_create_subscription.assert_called_once_with(expected_request, metadata=(("key", "value"),))
        assert result == expected_result

    def test_get_all_products(self, fxt_grpc_client) -> None:
        # Arrange
        grpc_response = ProductResponse(
            products=ProductsList(
                products=[
                    Product(
                        id="product_id_123",
                        name="Default",
                        created=12345,
                        updated=12345,
                        product_policies=[
                            ProductPolicy(
                                account_name="Default", init_amount=1000, renewable_amount=0, expires_in=456789
                            )
                        ],
                    )
                ]
            )
        )
        with patch.object(
            fxt_grpc_client.products_service_stub, "get_all_products", return_value=grpc_response
        ) as mocked_get_products:
            # Act
            result = fxt_grpc_client.get_all_products()

        # Assert
        mocked_get_products.assert_called_once()
        assert result.products[0].id == "product_id_123"

    def test_get_all_products_failure(self, fxt_grpc_client) -> None:
        # Arrange
        with (
            patch.object(
                fxt_grpc_client.products_service_stub,
                "get_all_products",
                side_effect=_InactiveRpcError(
                    state=_RPCState(
                        code=grpc.StatusCode.INTERNAL,
                        details="error details",
                        trailing_metadata=None,
                        initial_metadata=None,
                        due=[],
                    )
                ),
            ) as mocked_get_products,
            pytest.raises(grpc.RpcError),
        ):
            # Act
            fxt_grpc_client.get_all_products()

        # Assert
        mocked_get_products.assert_called_once()

    def test_get_quota(self, fxt_grpc_client) -> None:
        # Arrange
        grpc_response = QuotaGetResponse(
            quota_info=QuotaInfo(
                id=None,
                organization_id="org_id_123",
                service_name="jobs ms",
                quota_type=QuotaType.MAX_TRAINING_JOBS,
                quota_name="jobs limit",
                limit=10,
            )
        )
        with patch.object(fxt_grpc_client.quotas_service_stub, "get", return_value=grpc_response) as mocked_get_quota:
            # Act
            result = fxt_grpc_client._get_quota("org_id_123", QuotaType.MAX_TRAINING_JOBS)

        # Assert
        mocked_get_quota.assert_called_once()
        assert result.limit == 10

    def test_get_quota_failure(self, fxt_grpc_client) -> None:
        # Arrange
        with (
            patch.object(
                fxt_grpc_client.quotas_service_stub,
                "get",
                side_effect=_InactiveRpcError(
                    state=_RPCState(
                        code=grpc.StatusCode.INTERNAL,
                        details="error details",
                        trailing_metadata=None,
                        initial_metadata=None,
                        due=[],
                    )
                ),
            ) as mocked_get_quota,
            pytest.raises(grpc.RpcError),
        ):
            # Act
            fxt_grpc_client._get_quota("org_id_123", QuotaType.MAX_TRAINING_JOBS)

        # Assert
        mocked_get_quota.assert_called_once()
