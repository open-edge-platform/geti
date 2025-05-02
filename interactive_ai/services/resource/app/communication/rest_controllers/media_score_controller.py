# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from communication.exceptions import ModelTestResultNotFoundException
from communication.rest_data_validator.media_score_query_validator import MediaScoreQueryValidator
from communication.rest_views.media_score_rest_views import MediaScoreRESTViews
from managers.annotation_manager import AnnotationManager
from managers.project_manager import ProjectManager
from usecases.dataset_filter import DatasetFilter, DatasetFilterSortDirection, MediaScoreFilterField
from usecases.query_builder import QueryBuilder

from geti_fastapi_tools.exceptions import BadRequestException
from geti_types import ID
from iai_core_py.entities.model_test_result import NullModelTestResult, TestState
from iai_core_py.repos import DatasetRepo, MediaScoreRepo, ModelTestResultRepo


class MediaScoreRESTController:
    @staticmethod
    def get_filtered_items(
        project_id: ID,
        model_test_result_id: ID,
        sort_by: MediaScoreFilterField,
        sort_direction: DatasetFilterSortDirection,
        limit: int,
        skip: int,
        query: dict,
    ) -> dict:
        """
        Get filtered items for a given model test result id.

        :param project_id: The id of the project containing the test result
        :param model_test_result_id: The id of the model test result
        :param sort_by: Sorting field to sort by
        :param sort_direction: Sorting direction
        :param limit: Maximum number of results to return
        :param skip: Number of results to skip
        :param query: The query body
        :return: RESTView object representing the filtered results
        """
        project = ProjectManager.get_project_by_id(project_id=project_id)
        model_test_result = ModelTestResultRepo(project.identifier).get_by_id(model_test_result_id)
        if isinstance(model_test_result, NullModelTestResult):
            raise ModelTestResultNotFoundException(model_test_result_id)
        if model_test_result.state != TestState.DONE:
            raise BadRequestException(f"Test '{model_test_result.name}' has not produced results yet")

        MediaScoreQueryValidator().validate_media_score_query(query)

        media_score_filter = DatasetFilter.from_dict(
            limit=limit,
            skip=skip,
            sort_by=sort_by,
            sort_direction=sort_direction,
            query=query,
        )
        dataset_storage = model_test_result.get_dataset_storages()[0]
        query_results = QueryBuilder.get_results_for_media_scores_dataset_filter(
            dataset_filter=media_score_filter,
            dataset_storage_identifier=dataset_storage.identifier,
            model_test_result_id=model_test_result_id,
        )

        media_anno_states_per_task = AnnotationManager.get_media_states_per_task(
            project=project,
            dataset_storage_identifier=dataset_storage.identifier,
            media_identifiers=query_results.media_identifiers,
        )

        dataset_repo = DatasetRepo(dataset_storage.identifier)
        media_score_repo = MediaScoreRepo(dataset_storage.identifier)
        media_score_per_media_identifier = {}
        annotation_id_per_media_identifier = {}
        prediction_id_per_media_identifier = {}

        for query_result in query_results.media_query_results:
            media_identifier = query_result.media_identifier
            media_score_per_media_identifier[media_identifier] = media_score_repo.get_by_test_and_media_identifier(
                model_test_result.id_, media_identifier
            )
            annotation_id_per_media_identifier[media_identifier] = (
                dataset_repo.get_latest_annotation_scene_id(
                    dataset_id=model_test_result.ground_truth_dataset_id,
                    media_identifier=media_identifier,
                )
                if model_test_result.ground_truth_dataset_id
                else ID()
            )
            prediction_id_per_media_identifier[media_identifier] = (
                dataset_repo.get_latest_annotation_scene_id(
                    dataset_id=model_test_result.prediction_dataset_id,
                    media_identifier=media_identifier,
                )
                if model_test_result.prediction_dataset_id
                else ID()
            )

        return MediaScoreRESTViews.media_scores_to_rest(
            project=project,
            model_test_result=model_test_result,
            query_results=query_results,
            dataset_filter=media_score_filter,
            media_annotation_states_per_task=media_anno_states_per_task,
            media_score_per_media_identifier=media_score_per_media_identifier,
            annotation_id_per_media_identifier=annotation_id_per_media_identifier,
            prediction_id_per_media_identifier=prediction_id_per_media_identifier,
        )
