# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

import logging
from typing import TYPE_CHECKING

from behave import given
from behave.runner import Context

if TYPE_CHECKING:
    from geti_client import OrganizationsApi, PersonalAccessTokenOrganization200Response, WorkspacesApi

logger = logging.getLogger(__name__)


@given("a workspace")
def step_given_workspace(context: Context) -> None:
    """
    Requires context:
    - organizations_api
    - workspaces_api

    Sets context:
    - organization_id
    - workspace_id
    """
    org_api: OrganizationsApi = context.organizations_api
    ws_api: WorkspacesApi = context.workspaces_api

    pat_org_response: PersonalAccessTokenOrganization200Response = org_api.personal_access_token_organization()
    context.organization_id = pat_org_response.organization_id

    ws_response = ws_api.get_all_workspaces(organization_id=context.organization_id)
    if len(ws_response.workspaces) == 0:
        raise AssertionError(f"No workspaces found in organization {context.organization_id}")
    if len(ws_response.workspaces) > 1:
        logger.warning(f"Multiple workspaces found in organization {context.organization_id}. Using the first one.")
    context.workspace_id = ws_response.workspaces[0].id
