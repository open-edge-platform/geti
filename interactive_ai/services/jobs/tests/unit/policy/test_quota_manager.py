# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import MagicMock, patch

from policies.quota import get_organization_job_quota

from geti_types import ID


@patch("policies.quota.CreditSystemClient", autospec=True)
def test_get_organization_job_quota(mock_credits_service_client, request) -> None:
    # Arrange
    client = MagicMock()
    mock_credits_service_client.return_value = client
    client.__enter__.return_value = client
    client.get_jobs_quota.return_value = 10

    # Act
    quota = get_organization_job_quota(organization_id=ID("000000000000000000000001"))

    # Assert
    assert quota == 10
    client.get_jobs_quota.assert_called_once_with(organization_id="000000000000000000000001")
