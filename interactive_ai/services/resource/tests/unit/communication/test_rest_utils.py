# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from pathlib import Path

from starlette.responses import FileResponse, RedirectResponse

from communication.constants import DEFAULT_N_PROJECTS_RETURNED
from communication.rest_utils import project_query_data, send_file_from_path_or_url

from iai_core_py.repos.project_repo_helpers import ProjectQueryData, ProjectSortBy, ProjectSortDirection, SortDirection


class TestRestUtils:
    def test_send_media_from_path(self, fxt_resource_rest, fxt_mongo_id) -> None:
        response = send_file_from_path_or_url(
            request_host="dummy.ip",
            file_location=Path("dummy_path"),
            mimetype="image/jpeg",
        )
        assert isinstance(response, FileResponse)

    def test_send_media_from_url(self, fxt_resource_rest, fxt_mongo_id) -> None:
        response = send_file_from_path_or_url(
            request_host="dummy.ip",
            file_location="dummy_url",
            mimetype="image/jpeg",
        )
        assert isinstance(response, RedirectResponse)

    def test_get_project_query_data(self):
        result = project_query_data(
            skip=10,
            limit=50,
            name="",
            sort_by=ProjectSortBy.NAME,
            sort_direction=SortDirection.ASC,
            with_size=False,
        )

        assert result == ProjectQueryData(
            skip=10,
            limit=50,
            name="",
            sort_by=ProjectSortBy.NAME,
            sort_direction=ProjectSortDirection.ASC,
            with_size=False,
        )

    def test_get_project_query_data_default_values(self):
        assert project_query_data() == ProjectQueryData(
            skip=0,
            limit=DEFAULT_N_PROJECTS_RETURNED,
            name="",
            sort_by=ProjectSortBy.CREATION_DATE,
            sort_direction=ProjectSortDirection.DSC,
            with_size=False,
        )
