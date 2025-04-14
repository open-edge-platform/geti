# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from communication.constants import MAX_SETTINGS_LENGTH_IN_CHARACTERS
from communication.exceptions import NoUserSettingsException, SettingsTooLongException
from entities.ui_settings import NullUISettings, UISettings
from repos.ui_settings_repo import UISettingsRepo

from geti_fastapi_tools.dependencies import (
    get_optional_project_id,
    get_request_json,
    get_user_id_fastapi,
    setup_default_session_fastapi,
)
from geti_fastapi_tools.exceptions import BadRequestException
from geti_fastapi_tools.responses import success_response_rest
from geti_types import ID

# Override the session to a default value, since these endpoints do not have an organization/workspace.
# Otherwise it may incorrectly reuse the session previously set by another request handled by the same thread.
server_router = APIRouter(prefix="/api/v1", tags=["Server"], dependencies=[Depends(setup_default_session_fastapi)])

ProjectID = Annotated[ID | None, Query()]


@server_router.get("/user_settings")
def get_user_settings(
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
    project_id: ID = Depends(get_optional_project_id),  # noqa: FAST002
) -> dict:
    """
    Endpoint to get user settings, either on server or on project level.
    """
    ui_settings_repo = UISettingsRepo()
    if project_id is not None:
        ui_settings = ui_settings_repo.get_by_user_id_and_project(user_id=user_id, project_id=project_id)
    else:
        ui_settings = ui_settings_repo.get_by_user_id_only(user_id=user_id)
    if not isinstance(ui_settings, NullUISettings):
        return {"settings": ui_settings.settings}
    raise NoUserSettingsException


@server_router.post("/user_settings")
def post_user_settings(
    request_json: Annotated[dict, Depends(get_request_json)],
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
    project_id: ID = Depends(get_optional_project_id),  # noqa: FAST002
) -> dict:
    """
    Endpoint to post user settings, either on server or on project level.
    """
    ui_settings_repo = UISettingsRepo()
    try:
        settings = str(request_json["settings"])
    except KeyError:
        raise BadRequestException("No settings supplied in the body of the request.")

    if len(settings) > MAX_SETTINGS_LENGTH_IN_CHARACTERS:
        raise SettingsTooLongException(MAX_SETTINGS_LENGTH_IN_CHARACTERS)
    # Get the id of the old settings for overwriting.
    if project_id is not None:
        old_settings_id = ui_settings_repo.get_by_user_id_and_project(user_id=user_id, project_id=project_id).id_
    else:
        old_settings_id = ui_settings_repo.get_by_user_id_only(user_id=user_id).id_
    # Set the new settings.
    user_settings = UISettings(
        user_id=user_id,
        project_id=project_id if project_id is not None else None,
        settings=settings,
        id_=old_settings_id if old_settings_id != ID() else ui_settings_repo.generate_id(),
    )
    ui_settings_repo.save(user_settings)
    return success_response_rest()
