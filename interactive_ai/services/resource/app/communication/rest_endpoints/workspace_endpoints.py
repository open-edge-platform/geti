# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

from fastapi import APIRouter
from starlette.responses import JSONResponse

from geti_types import CTX_SESSION_VAR, ID, make_session

logger = logging.getLogger(__name__)


workspace_router = APIRouter(prefix="/api/v1/organizations/{organization_id}", tags=["Workspace"])


@workspace_router.get("/workspaces")
def get_workspaces(organization_id: str) -> JSONResponse:
    """Get all the workspaces"""
    # TODO CVS-113447 remove this endpoint after account service is enabled
    # Note: make_session is a workaround to prevent the repo from throwing an exception due to missing session context;
    #   only needs 'organization_id' and this endpoint is going to be removed anyway.
    session = make_session(organization_id=ID(organization_id))
    CTX_SESSION_VAR.set(session)
    return JSONResponse(content={})
