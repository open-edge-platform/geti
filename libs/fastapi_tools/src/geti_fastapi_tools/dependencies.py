import datetime
from json import JSONDecodeError
from typing import Annotated, Any
from uuid import UUID

from bson import ObjectId
from fastapi import Depends, Query, Request
from geti_types.id import ID, DatasetStorageIdentifier, ProjectIdentifier
from geti_types.session import (
    CTX_SESSION_VAR,
    DEFAULT_ORGANIZATION_ID,
    DEFAULT_WORKSPACE_ID,
    RequestSource,
    make_session,
)

from geti_fastapi_tools.exceptions import (
    InvalidIDException,
    MissingPayloadException,
    MissingRequestAccessTokenException,
)
from geti_fastapi_tools.identity import RestApiAuth


async def get_request_body(request: Request) -> bytes:
    """Get the body of the FastAPI request"""
    return await request.body()


async def get_request_json(request: Request) -> dict:
    """Get the JSON payload of the FastAPI request"""
    try:
        return await request.json()
    except JSONDecodeError:
        raise MissingPayloadException


async def get_optional_request_json(request: Request) -> dict | None:
    """Get the JSON payload of the FastAPI request if it exists, otherwise return None"""
    try:
        return await request.json()
    except Exception:
        return None


def is_valid_objectid(identifier: str) -> bool:
    """
    Check if a given string identifier is formatted as a valid ObjectId

    :param identifier: String to check
    :return: True if valid ObjectId, False otherwise
    """
    return ObjectId.is_valid(identifier)


def is_valid_uuid(identifier: str) -> bool:
    """
    Check if a given string identifier is formatted as a valid UUID

    :param identifier: String to check
    :return: True if valid UUID, False otherwise
    """
    try:
        UUID(identifier)
    except ValueError:
        return False
    return True


def is_valid_id(identifier: str) -> bool:
    """
    Check if a given string identifier is formatted as a valid ID (ObjectId-like or UUID-like)

    :param identifier: String to check
    :return: True if valid ObjectId, False otherwise
    """
    return is_valid_uuid(identifier) or is_valid_objectid(identifier)


def get_organization_id(organization_id: str) -> ID:
    """Initializes and validates an organization ID"""
    if not is_valid_uuid(organization_id):
        raise InvalidIDException(id_name="organization_id", invalid_id=str(organization_id))
    return ID(organization_id)


def get_workspace_id(workspace_id: str) -> ID:
    """Initializes and validates a workspace ID"""
    if not is_valid_id(workspace_id):
        raise InvalidIDException(id_name="workspace_id", invalid_id=str(workspace_id))
    return ID(workspace_id)


def get_project_id(project_id: str) -> ID:
    """Initializes and validates a project ID"""
    if not is_valid_objectid(project_id):
        raise InvalidIDException(id_name="project_id", invalid_id=project_id)
    return ID(project_id)


def get_dataset_id(dataset_id: str) -> ID:
    """Initializes and validates a dataset storage ID"""
    if not is_valid_objectid(dataset_id):
        raise InvalidIDException(id_name="dataset_id", invalid_id=dataset_id)
    return ID(dataset_id)


def get_project_identifier(workspace_id: str, project_id: str) -> ProjectIdentifier:
    """
    Can be used as a dependency in a FastAPI endpoint to create a project identifier from
    a workspace_id and project_id
    """
    workspace_id_ = get_workspace_id(workspace_id)
    project_id_ = get_project_id(project_id)
    return ProjectIdentifier(
        workspace_id=workspace_id_,
        project_id=project_id_,
    )


def get_dataset_storage_identifier(workspace_id: str, project_id: str, dataset_id: str) -> DatasetStorageIdentifier:
    """Initializes and validates a DatasetStorageIdentifier"""
    workspace_id_ = get_workspace_id(workspace_id)
    project_id_ = get_project_id(project_id)
    dataset_storage_id_ = get_dataset_id(dataset_id)
    return DatasetStorageIdentifier(
        workspace_id=workspace_id_,
        project_id=project_id_,
        dataset_storage_id=dataset_storage_id_,
    )


def get_image_id(image_id: str) -> ID:
    """Initializes and validates a image ID"""
    if not is_valid_objectid(image_id):
        raise InvalidIDException(id_name="image_id", invalid_id=image_id)
    return ID(image_id)


def get_video_id(video_id: str) -> ID:
    """Initializes and validates a video ID"""
    if not is_valid_objectid(video_id):
        raise InvalidIDException(id_name="video_id", invalid_id=video_id)
    return ID(video_id)


def get_annotation_id(annotation_id: str) -> ID:
    """Initializes and validates an annotation ID"""
    # Do not validate in case user requests latest
    if annotation_id == "latest":
        return ID(annotation_id)
    if not is_valid_objectid(annotation_id):
        raise InvalidIDException(id_name="annotation_id", invalid_id=annotation_id)
    return ID(annotation_id)


def get_deployment_id(deployment_id: str) -> ID:
    """Initializes and validates a code deployment ID"""
    if not is_valid_objectid(deployment_id):
        raise InvalidIDException(id_name="deployment_id", invalid_id=deployment_id)
    return ID(deployment_id)


def get_dataset_revision_id(dataset_revision_id: str) -> ID:
    """Initializes and validates a dataset ID"""
    if not is_valid_objectid(dataset_revision_id):
        raise InvalidIDException(id_name="dataset_revision_id", invalid_id=dataset_revision_id)
    return ID(dataset_revision_id)


def get_test_id(test_id: str) -> ID:
    """ "Initializes and validates a model test ID"""
    if not is_valid_objectid(test_id):
        raise InvalidIDException(id_name="test_id", invalid_id=test_id)
    return ID(test_id)


def get_model_group_id(model_group_id: str) -> ID:
    """ "Initializes and validates a model group ID"""
    if not is_valid_objectid(model_group_id):
        raise InvalidIDException(id_name="model_group_id", invalid_id=model_group_id)
    return ID(model_group_id)


def get_model_id(model_id: str) -> ID:
    """ "Initializes and validates a model ID"""
    if not is_valid_objectid(model_id):
        raise InvalidIDException(id_name="model_id", invalid_id=model_id)
    return ID(model_id)


def get_file_id(file_id: str) -> ID:
    """Initializes and validates a file ID"""
    if not is_valid_objectid(file_id):
        raise InvalidIDException(id_name="file", invalid_id=file_id)
    return ID(file_id)


def get_optimized_model_id(optimized_model_id: str) -> ID:
    """Initializes and validates an optimized model ID"""
    if not is_valid_objectid(optimized_model_id):
        raise InvalidIDException(id_name="optimized_model_id", invalid_id=optimized_model_id)
    return ID(optimized_model_id)


def get_task_id(task_id: str) -> ID:
    """Initializes and validates a task ID"""
    if not is_valid_objectid(task_id):
        raise InvalidIDException(id_name="task_id", invalid_id=task_id)
    return ID(task_id)


def get_prediction_id(prediction_id: str) -> ID:
    """Initializes and validates a prediction ID"""
    if not is_valid_objectid(prediction_id):
        raise InvalidIDException(id_name="prediction_id", invalid_id=prediction_id)
    return ID(prediction_id)


def get_optional_task_id(task_id: str | None = None) -> ID | None:
    """Initializes and validates an optional Task ID"""
    if task_id is None:
        return None
    if not is_valid_objectid(task_id):
        raise InvalidIDException(id_name="task_id", invalid_id=task_id)
    return ID(task_id)


def get_optional_model_id(model_id: str | None = None) -> ID | None:
    """Initializes and validates an optional Model ID"""
    if model_id is None:
        return None
    if not is_valid_objectid(model_id):
        raise InvalidIDException(id_name="model_id", invalid_id=model_id)
    return ID(model_id)


def get_optional_project_id(project_id: str | None = None) -> ID | None:
    """Initializes and validates an optional Project ID"""
    if project_id is None:
        return None
    if not is_valid_objectid(project_id):
        raise InvalidIDException(id_name="project_id", invalid_id=project_id)
    return ID(project_id)


def get_skiptoken(skiptoken: Annotated[str | None, Query()] = None) -> ID:
    """Initializes and validates a skiptoken ID"""
    if skiptoken is None:
        return ID(ObjectId.from_datetime(datetime.datetime(1970, 1, 1)))
    if not is_valid_objectid(skiptoken):
        raise InvalidIDException(id_name="skiptoken", invalid_id=skiptoken)
    return ID(skiptoken)


def get_user_id_fastapi(request: Request) -> ID:
    """
    Get the user ID from a FastAPI request

    :param request: FastAPI request object
    :return: ID of the user
    """
    return ID(RestApiAuth.get_user_id(request.headers))


def get_source_fastapi(request: Request) -> RequestSource:
    """
    Get the 'source' claim from the JWT token attached to a FastAPI request

    :param request: FastAPI request object
    :return: RequestSource representing the 'source'
    """
    try:
        raw_source = RestApiAuth.get_source(request.headers)
    except MissingRequestAccessTokenException:
        # The source header is not mandatory for inbound requests (i.e. issued by other internal services)
        return RequestSource.INTERNAL
    match raw_source:
        case "browser":
            return RequestSource.BROWSER
        case "pat":
            return RequestSource.API_KEY
        case _:
            return RequestSource.UNKNOWN


def parse_time(t: str | None) -> datetime.datetime | None:
    """Parse ISO format time string to datetime object."""
    return datetime.datetime.fromisoformat(t) if t else None


async def setup_session_fastapi(
    organization_id: str,
    workspace_id: str,
    request_source: Annotated[RequestSource, Depends(get_source_fastapi)],
) -> None:
    """
    Initialize the Session for FastAPI endpoints, and store it in CTX_SESSION_VAR
    """
    session = make_session(organization_id=ID(organization_id), workspace_id=ID(workspace_id), source=request_source)
    CTX_SESSION_VAR.set(session)


async def setup_default_session_fastapi() -> Any:
    """
    Decorator for FastAPI endpoints to initialize a default session and store it in CTX_SESSION_VAR

    This decorator should be only used for endpoints that are not prefixed with a specific organization/workspace.
    """
    session = make_session(
        organization_id=DEFAULT_ORGANIZATION_ID, workspace_id=DEFAULT_WORKSPACE_ID, source=RequestSource.UNKNOWN
    )
    CTX_SESSION_VAR.set(session)
