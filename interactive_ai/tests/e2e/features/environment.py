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
import os
from pathlib import Path

import urllib3
from behave import fixture, use_fixture
from behave.runner import Context
from geti_client import (
    ActiveLearningApi,
    AnnotationsApi,
    ApiClient,
    ApiException,
    Configuration,
    ConfigurationApi,
    DatasetImportExportApi,
    DatasetsApi,
    DeploymentPackageApi,
    JobsApi,
    MediaApi,
    ModelsApi,
    OrganizationsApi,
    PredictionsApi,
    ProjectImportExportApi,
    ProjectsApi,
    TestsApi,
    TrainingDatasetVersionsApi,
    WorkspacesApi,
)

BEHAVE_DEBUG_ON_ERROR = True


def setup_debug_on_error(userdata) -> None:
    global BEHAVE_DEBUG_ON_ERROR  # noqa: PLW0603
    BEHAVE_DEBUG_ON_ERROR = userdata.getbool("BEHAVE_DEBUG_ON_ERROR")


@fixture
def fxt_geti_server_config(context: Context) -> Configuration:  # noqa: ARG001
    geti_server_url = os.environ.get("GETI_SERVER_URL")
    if not geti_server_url:
        raise OSError("GETI_SERVER_URL env variable is not set")

    geti_api_key = os.environ.get("GETI_API_KEY")
    if not geti_api_key:
        raise OSError("GETI_API_KEY env variable is not set")

    if geti_server_url.endswith("/"):
        geti_server_url = geti_server_url.removesuffix("/")

    geti_api_base_url = f"{geti_server_url}/api/v1"
    geti_server_config = Configuration(host=geti_api_base_url)
    geti_server_config.api_key["ApiKeyAuth"] = geti_api_key
    geti_server_config.verify_ssl = False
    yield geti_server_config


@fixture
def fxt_api_client(context: Context) -> ApiClient:
    geti_server_config = use_fixture(fxt_geti_server_config, context)
    context.api_client = ApiClient(
        configuration=geti_server_config,
        header_name="X-Geti-Csrf-Protection",
        header_value="1",
    )
    yield context.api_client


@fixture
def fxt_active_learning_api(context: Context) -> ActiveLearningApi:
    with context.api_client as api_client:
        context.active_learning_api = ActiveLearningApi(api_client)
        yield context.active_learning_api


@fixture
def fxt_annotations_api(context: Context) -> AnnotationsApi:
    with context.api_client as api_client:
        context.annotations_api = AnnotationsApi(api_client)
        yield context.annotations_api


@fixture
def fxt_configuration_api(context: Context) -> ConfigurationApi:
    with context.api_client as api_client:
        context.configuration_api = ConfigurationApi(api_client)
        yield context.configuration_api


@fixture
def fxt_dataset_import_export_api(context: Context) -> DatasetImportExportApi:
    with context.api_client as api_client:
        context.dataset_import_export_api = DatasetImportExportApi(api_client)
        yield context.dataset_import_export_api


@fixture
def fxt_datasets_api(context: Context) -> DatasetsApi:
    with context.api_client as api_client:
        context.datasets_api = DatasetsApi(api_client)
        yield context.datasets_api


@fixture
def fxt_deployment_package_api(context: Context) -> DeploymentPackageApi:
    with context.api_client as api_client:
        context.deployment_package_api = DeploymentPackageApi(api_client)
        yield context.deployment_package_api


@fixture
def fxt_jobs_api(context: Context) -> JobsApi:
    with context.api_client as api_client:
        context.jobs_api = JobsApi(api_client)
        yield context.jobs_api


@fixture
def fxt_media_api(context: Context) -> MediaApi:
    with context.api_client as api_client:
        context.media_api = MediaApi(api_client)
        yield context.media_api


@fixture
def fxt_models_api(context: Context) -> ModelsApi:
    with context.api_client as api_client:
        context.models_api = ModelsApi(api_client)
        yield context.models_api


@fixture
def fxt_organizations_api(context) -> OrganizationsApi:
    with context.api_client as api_client:
        context.organizations_api = OrganizationsApi(api_client)
        yield context.organizations_api


@fixture
def fxt_predictions_api(context: Context) -> PredictionsApi:
    with context.api_client as api_client:
        context.predictions_api = PredictionsApi(api_client)
        yield context.predictions_api


@fixture
def fxt_project_import_export_api(context: Context) -> ProjectImportExportApi:
    with context.api_client as api_client:
        context.project_import_export_api = ProjectImportExportApi(api_client)
        yield context.project_import_export_api


@fixture
def fxt_projects_api(context: Context) -> ProjectsApi:
    with context.api_client as api_client:
        context.projects_api = ProjectsApi(api_client)
        yield context.projects_api


@fixture
def fxt_tests_api(context: Context) -> TestsApi:
    with context.api_client as api_client:
        context.tests_api = TestsApi(api_client)
        yield context.tests_api


@fixture
def fxt_training_dataset_versions_api(context: Context) -> TrainingDatasetVersionsApi:
    with context.api_client as api_client:
        context.training_dataset_versions_api = TrainingDatasetVersionsApi(api_client)
        yield context.training_dataset_versions_api


@fixture
def fxt_workspaces_api(context: Context) -> WorkspacesApi:
    with context.api_client as api_client:
        context.workspaces_api = WorkspacesApi(api_client)
        yield context.workspaces_api


def _cleanup_project(context: Context) -> None:
    projects_api: ProjectsApi = context.projects_api
    project_id = getattr(context, "project_id", None)
    if project_id is not None:
        projects_api.delete_project(
            organization_id=context.organization_id,
            workspace_id=context.workspace_id,
            project_id=project_id,
        )
        delattr(context, "project_id")


def _setup_data_dirs(context: Context) -> None:
    context.data_base_dir = Path(__file__).parent.parent / "data"
    os.makedirs(context.data_base_dir, exist_ok=True)

    context.images_dir = context.data_base_dir / "images"
    os.makedirs(context.images_dir, exist_ok=True)

    context.datasets_dir = context.data_base_dir / "datasets"
    os.makedirs(context.datasets_dir, exist_ok=True)

    context.projects_dir = context.data_base_dir / "projects"
    os.makedirs(context.projects_dir, exist_ok=True)


def before_all(context: Context) -> None:
    if not context.config.log_capture:
        logging.basicConfig(level=logging.INFO)
        logging.getLogger("urllib3.poolmanager").setLevel(logging.WARNING)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    setup_debug_on_error(context.config.userdata)

    use_fixture(fxt_api_client, context)

    use_fixture(fxt_active_learning_api, context)
    use_fixture(fxt_annotations_api, context)
    use_fixture(fxt_configuration_api, context)
    use_fixture(fxt_dataset_import_export_api, context)
    use_fixture(fxt_datasets_api, context)
    use_fixture(fxt_deployment_package_api, context)
    use_fixture(fxt_jobs_api, context)
    use_fixture(fxt_media_api, context)
    use_fixture(fxt_models_api, context)
    use_fixture(fxt_organizations_api, context)
    use_fixture(fxt_predictions_api, context)
    use_fixture(fxt_project_import_export_api, context)
    use_fixture(fxt_projects_api, context)
    use_fixture(fxt_tests_api, context)
    use_fixture(fxt_training_dataset_versions_api, context)
    use_fixture(fxt_workspaces_api, context)

    _setup_data_dirs(context)


def after_step(context, step) -> None:  # noqa: ARG001
    if BEHAVE_DEBUG_ON_ERROR and step.status == "failed":
        import pdb

        pdb.post_mortem(step.exc_traceback)


def after_scenario(context: Context, scenario) -> None:  # noqa: ARG001
    try:
        _cleanup_project(context)
    except ApiException as e:
        if e.status != 403:
            raise e
