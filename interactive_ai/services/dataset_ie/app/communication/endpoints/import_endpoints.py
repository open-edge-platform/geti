# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements the import endpoints
"""

import logging

from fastapi import APIRouter, Body, Depends, HTTPException
from starlette.responses import JSONResponse

from application.import_management import ImportManager
from communication.helpers.http_exceptions import BadRequestGetiBaseException, InternalServerErrorGetiBaseException
from communication.helpers.import_utils import ImportUtils
from communication.helpers.limit_check_helpers import check_max_number_of_labels, check_max_number_of_projects
from communication.helpers.validation_helpers import (
    get_validated_mongo_id,
    get_validated_project,
    get_validated_project_type_from_task_type,
)

from geti_fastapi_tools.dependencies import get_user_id_fastapi, setup_session_fastapi
from geti_fastapi_tools.exceptions import DatasetStorageNotFoundException, GetiBaseException
from geti_types import ID
from sc_sdk.entities.dataset_storage import NullDatasetStorage
from sc_sdk.repos import DatasetStorageRepo

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", dependencies=[Depends(setup_session_fastapi)])

UNKNOWN_ERROR_DURING_IMPORT = "Unknown error faced during dataset loading"


@router.post("/organizations/{organization_id}/workspaces/{workspace_id}/datasets:prepare-for-import")
def prepare_dataset_for_import_endpoint(
    file_id: str,
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
) -> JSONResponse:
    """
    Endpoint to prepare dataset for importing into a new project, by first converting to
    datumaro format, then collecting warnings and returning a mapping of labels to their
    possible domains.

    :param file_id: id of the uploaded dataset to prepare
    :param user_id: ID of the user who sent the request
    :return: warnings, mappings of each label to possible tasks
    """
    logger.info(f"Handling post `prepare_dataset_for_import_endpoint`: file_id={file_id}, user_id={user_id}")
    file_id = get_validated_mongo_id(id=file_id)
    check_max_number_of_projects()
    # validate file_id and metadata according to CVS-108914
    file_metadata = ImportManager().get_validated_file_metadata(file_id=file_id)

    job_metadata = {"file_id": str(file_metadata.id_)}

    logger.info("Feature flag for import jobs is enabled, submitting prepare import to new project job")
    try:
        job_id = ImportManager().submit_prepare_import_to_new_project_job(
            import_id=file_id, author=user_id, metadata=job_metadata
        )
    except Exception as e:
        logger.exception(f"Exception raised while submitting prepare_import_to_new_project job: {str(e)}")
        raise InternalServerErrorGetiBaseException(UNKNOWN_ERROR_DURING_IMPORT)
    logger.info(f"Submitted prepare import to new project job with id {job_id}")
    return JSONResponse({"job_id": job_id})


@router.post("/organizations/{organization_id}/workspaces/{workspace_id}/projects:import-from-dataset")
def import_project_from_dataset_endpoint(
    file_id: str = Body(...),  # noqa: FAST002
    project_name: str = Body(...),  # noqa: FAST002
    task_type: str = Body(...),  # noqa: FAST002
    labels: list[dict] = Body(...),  # noqa: FAST002
    keypoint_structure: dict[str, list[dict]] = Body(default={"edges": [], "positions": []}),  # noqa: FAST002
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
) -> JSONResponse:
    """
    Endpoint to create a project and load the prepared datumaro dataset into it.

    :param file_id: id of datumaro dataset to load into created project
    :param project_name: Name of the project
    :param task_type: REST task type name of the project based on GetiProjectType
    :param labels: list of labels to keep
    :param keypoint_structure: keypoints edges and positions of default template
    :param user_id: ID of the user who sent the request
    :return: id of the project
    """
    logger.info(
        f"Handling post `import_project_from_dataset_endpoint`: file_id={file_id}, "
        f"project_name={project_name}, task_type={task_type}, labels={labels}, "
        f"keypoint_structure={keypoint_structure}, user_id={user_id}"
    )
    file_id = get_validated_mongo_id(id=file_id)
    check_max_number_of_projects()
    check_max_number_of_labels(labels=labels)
    # validate file_id and metadata according to CVS-108914
    file_metadata = ImportManager().get_validated_file_metadata(file_id=file_id)
    # If the import is not running yet, start the import process.
    label_names = [label_meta["name"] for label_meta in labels]
    label_colors = {label_meta["name"]: label_meta["color"] for label_meta in labels if "color" in label_meta}
    project_type = get_validated_project_type_from_task_type(task_type)

    job_metadata = {"file_id": str(file_metadata.id_), "project": {"name": project_name, "type": task_type}}

    logger.info("Feature flag for import jobs is enabled, submitting perform import to new project job")
    try:
        job_id = ImportManager().submit_perform_import_to_new_project_job(
            import_id=file_id,
            project_type=project_type,
            project_name=project_name,
            label_names=label_names,
            color_by_label=label_colors,
            keypoint_structure=keypoint_structure,
            author=user_id,
            metadata=job_metadata,
        )
    except Exception as e:
        logger.exception(f"Exception raised while submitting perform_import_to_new_project job: {str(e)}")
        raise InternalServerErrorGetiBaseException(UNKNOWN_ERROR_DURING_IMPORT)

    logger.info(f"Submitted perform import to new project job with id {job_id}")
    return JSONResponse({"job_id": job_id})


@router.post(
    "/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}/datasets:prepare-for-import"
)
def prepare_dataset_for_import_to_existing_project_endpoint(
    project_id: str,
    file_id: str,
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
) -> dict:
    """
    Endpoint to prepare the dataset for importing into an existing project.
    Loads the dataset from the file in datumaro format, validates the dataset ands collects
    any warnings, and collects the labels in the dataset.

    :param project_id: id of project to import dataset to
    :param file_id: id of dataset to load into created project
    :param user_id: ID of the user who sent the request
    :return: warnings, list of labels in the dataset
    """
    logger.info(
        f"Handling post `prepare_dataset_for_import_to_existing_project_endpoint`: project_id={project_id}, "
        f"file_id={file_id}, user_id={user_id}"
    )
    file_id = get_validated_mongo_id(id=file_id)

    try:
        # validate file_id and metadata according to CVS-108914
        file_metadata = ImportManager().get_validated_file_metadata(file_id=file_id)

        # validate project
        project = get_validated_project(project_id=project_id)
        ImportManager().save_project_id(file_id=file_id, project_id=ID(project_id))

        # validate task_type
        try:
            _ = ImportUtils.get_validated_task_type(project=project)
        except ValueError as e:
            raise BadRequestGetiBaseException(str(e))

        job_metadata = {
            "file_id": str(file_metadata.id_),
            "project": {
                "id": project_id,
                "name": project.name,
                "type": ImportUtils.project_type_to_rest_api_string(ImportUtils.get_project_type(project)),
            },
        }

        logger.info("Feature flag for import jobs is enabled, submitting prepare import to existing project job")
        job_id = ImportManager().submit_prepare_import_to_existing_project_job(
            project_id=ID(project_id),
            import_id=file_id,
            author=user_id,
            metadata=job_metadata,
        )
    except HTTPException as e:
        raise e
    except GetiBaseException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)
    except Exception as e:
        logger.exception(f"Exception raised while submitting prepare_import_to_existing_project job: {str(e)}")
        raise InternalServerErrorGetiBaseException(UNKNOWN_ERROR_DURING_IMPORT)
    logger.info(f"Submitted prepare import to new project job with id {job_id}")
    return {"job_id": job_id}


@router.post("/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}:import-from-dataset")
def import_dataset_to_project_endpoint(
    project_id: str,
    file_id: str = Body(...),  # noqa: FAST002
    dataset_id: str = Body(...),  # noqa: FAST002
    dataset_name: str = Body(...),  # noqa: FAST002
    labels_map: dict[str, str] = Body(...),  # noqa: FAST002
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
) -> JSONResponse:
    """
    Endpoint to import an already prepared dataset to an existing project. If a dataset_id
    is provided then it will import into that dataset. If a dataset_name is provided then
    a new dataset will be created with the provided name. The labels_map provides a map of
    the prepared dataset's labels to the project's labels.

    :param project_id: id of project to load dataset into
    :param file_id: id of uploaded and prepared datumaro dataset
    :param dataset_id: id of the dataset storage, if importing to an existing one
    :param dataset_name: name of the dataset storage, if importing to a new one
    :param labels_map: dictionary mapping datumaro label name to SC label id
    :param user_id: ID of the user who sent the request
    """
    logger.info(
        f"Handling post `import_dataset_to_project_endpoint`: project_id={project_id}, "
        f"file_id={file_id}, dataset_id={dataset_id}, dataset_name={dataset_name}, "
        f"labels_map={labels_map}, user_id={user_id}"
    )
    file_id = get_validated_mongo_id(id=file_id)

    try:
        # validate file_id and metadata according to CVS-108914
        file_metadata = ImportManager().get_validated_file_metadata(file_id=file_id)

        # validate project
        project = get_validated_project(project_id=project_id)

        # validate task type
        try:
            _ = ImportUtils.get_validated_task_type(project=project)
        except ValueError as e:
            raise BadRequestGetiBaseException(str(e))

        if ID(project_id) != file_metadata.project_id:
            raise BadRequestGetiBaseException(
                "Dataset with given id prepared for import into a project, but import attempted into different project"
            )

        # validate label_id regarding the bug CVS-129444
        ImportManager().validate_project_label_ids(project_id=project_id, label_ids_map=labels_map)
        dataset_name_: str | None
        if dataset_id:
            # validate dataset storage_id
            dataset_storage = DatasetStorageRepo(project.identifier).get_by_id(ID(dataset_id))
            if isinstance(dataset_storage, NullDatasetStorage):
                raise DatasetStorageNotFoundException(dataset_id)
            dataset_id_ = dataset_storage.id_
            dataset_name_ = dataset_storage.name
        else:
            dataset_id_ = None
            dataset_name_ = dataset_name if dataset_name else None

        job_metadata = {
            "file_id": str(file_metadata.id_),
            "project": {
                "id": project_id,
                "name": project.name,
                "type": ImportUtils.project_type_to_rest_api_string(ImportUtils.get_project_type(project)),
            },
            "dataset": {
                "id": dataset_id_,
                "name": dataset_name_,
            },
        }

        logger.info("submitting perform import to existing project job")
        job_id = ImportManager().submit_perform_import_to_existing_project_job(
            project_id=ID(project_id),
            import_id=file_id,
            labels_map=labels_map,
            dataset_storage_id=dataset_id_,
            dataset_name=dataset_name_,
            author=user_id,
            metadata=job_metadata,
        )
    except HTTPException:
        raise
    except GetiBaseException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)
    except Exception as e:
        logger.exception(f"Exception raised while submitting perform_import_to_existing_project job: {str(e)}")
        raise InternalServerErrorGetiBaseException(UNKNOWN_ERROR_DURING_IMPORT)
    logger.info(f"Submitted perform import to existing project job with id {job_id}")
    return JSONResponse({"job_id": job_id})
