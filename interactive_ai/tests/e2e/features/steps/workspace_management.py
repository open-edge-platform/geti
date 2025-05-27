# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
