"""This module implements RestValidator classes"""

# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

import json
import logging
import os

import jsonschema

from geti_fastapi_tools.validation import RestApiValidator

logger = logging.getLogger(__name__)


annotation_example_to_schema_map = {
    "annotations/requests/create_detection_annotation.json": "annotations/requests/annotation_scene_image.yaml",
    "annotations/requests/create_classification_annotation.json": "annotations/requests/annotation_scene_image.yaml",
    "annotations/requests/create_segmentation_annotation.json": "annotations/requests/annotation_scene_image.yaml",
    "annotations/requests/create_rotated_detection_annotation.json": "annotations/requests/annotation_scene_image.yaml",
    "annotations/responses/image_annotation_response.json": "annotations/responses/annotation_scene_image.yaml",
    "annotations/responses/video_frame_annotation_response.json": "annotations/responses/annotation_scene_video_"
    "frame.yaml",
    "annotations/responses/video_annotation_range_response.json": "annotations/responses/video_annotation_range.yaml",
}
configuration_example_to_schema_map = {
    "configuration/requests/full_configuration_request.json": "configuration/requests/full_configuration.yaml",
    "configuration/requests/global_configuration_request.json": "configuration/requests/global_configuration.yaml",
    "configuration/requests/task_configuration_request.json": "configuration/requests/task_configuration.yaml",
    "configuration/requests/task_chain_configuration_request.json": "configuration/requests"
    "/task_chain_configuration.yaml",
    "configuration/requests/task_configuration_request_hyper_param_groups.json": "configuration/requests"
    "/task_configuration.yaml",
    "configuration/responses/full_configuration_response.json": "configuration/responses/full_configuration.yaml",
    "configuration/responses/global_configuration_response.json": "configuration/responses/global_configuration.yaml",
    "configuration/responses/task_configuration_response.json": "configuration/responses/task_configuration.yaml",
    "configuration/responses/task_chain_configuration_response.json": "configuration/responses"
    "/task_chain_configuration.yaml",
    "configuration/responses/model_configuration_response.json": "configuration/responses/task_configuration.yaml",
}
dataset_example_to_schema_map = {
    "datasets/responses/active_dataset_response.json": "datasets/responses/active_set.yaml",
    "datasets/responses/dataset_statistics_response.json": "datasets/responses/dataset_statistics.yaml",
    "datasets/responses/filtered_dataset_response.json": "datasets/responses/filtered_dataset.yaml",
    "datasets/responses/filtered_video_frames.json": "datasets/responses/filtered_frames_in_video.yaml",
    "datasets/responses/dataset_info.json": "datasets/responses/dataset.yaml",
    "datasets/responses/updated_dataset_info.json": "datasets/responses/dataset.yaml",
    "datasets/responses/dataset_list_response.json": "datasets/responses/dataset_list.yaml",
    "datasets/requests/create_dataset.json": "datasets/requests/post/dataset.yaml",
    "datasets/requests/update_dataset.json": "datasets/requests/put/dataset.yaml",
}
job_example_to_schema_map = {
    "jobs/responses/multiple_jobs_response.json": "jobs/responses/job_list.yaml",
    "jobs/responses/single_job_id_response.json": "jobs/responses/job_id.yaml",
    "jobs/responses/train_scheduled.json": "jobs/responses/job_train.yaml",
    "jobs/responses/train_running.json": "jobs/responses/job_train.yaml",
    "jobs/responses/train_finished.json": "jobs/responses/job_train.yaml",
    "jobs/responses/train_cancelled.json": "jobs/responses/job_train.yaml",
    "jobs/responses/export_dataset.json": "jobs/responses/job_export_dataset.yaml",
    "jobs/responses/prepare_import_to_new_project.json": "jobs/responses/job_prepare_import_to_new_project.yaml",
    "jobs/responses/perform_import_to_new_project.json": "jobs/responses/job_perform_import_to_new_project.yaml",
    "jobs/responses/prepare_import_to_existing_project.json": "jobs/responses"
    "/job_prepare_import_to_existing_project.yaml",
    "jobs/responses/perform_import_to_existing_project.json": "jobs/responses/"
    "job_perform_import_to_existing_project.yaml",
    "jobs/responses/export_project.json": "jobs/responses/job_export_project.yaml",
    "jobs/responses/import_project.json": "jobs/responses/job_import_project.yaml",
    "jobs/responses/import_project_failed.json": "jobs/responses/job_import_project.yaml",
}
media_example_to_schema_map = {
    "media/responses/single_image.json": "media/responses/image.yaml",
    "media/responses/single_video.json": "media/responses/video.yaml",
}
model_example_to_schema_map = {
    "models/requests/optimization_request.json": "models/requests/optimization_request.yaml",
    "models/responses/model_detail_response.json": "models/responses/model_detail.yaml",
    "models/responses/model_group_list_response.json": "models/responses/model_group_list.yaml",
    "models/responses/model_group_response.json": "models/responses/model_group.yaml",
    "models/responses/model_statistics_response.json": "models/responses/model_statistics.yaml",
    "models/responses/supported_algorithms.json": "models/responses/supported_algorithm.yaml",
}
pipeline_example_to_schema_map = {
    "pipelines/responses/batch_explain_response.json": "pipelines/responses/batch_explanation.yaml",
    "pipelines/responses/batch_predict_response.json": "pipelines/responses/batch_prediction.yaml",
    "pipelines/responses/single_explain_response.json": "pipelines/responses/single_explanation.yaml",
    "pipelines/responses/single_predict_response.json": "pipelines/responses/single_prediction.yaml",
    "pipelines/responses/single_predict_response_media_identifier.json": "pipelines/responses/single_prediction.yaml",
}
project_example_to_schema_map = {
    "projects/requests/post/classification_project_request.json": "projects/requests/post/project.yaml",
    "projects/requests/post/segmentation_project_request.json": "projects/requests/post/project.yaml",
    "projects/requests/post/classification_label_hierarchy_project_request.json": "projects/requests/post/project.yaml",
    "projects/requests/post/keypoint_detection_project_request.json": "projects/requests/post/project.yaml",
    "projects/requests/post/single_detection_project_request.json": "projects/requests/post/project.yaml",
    "projects/requests/post/task_chain_project_request.json": "projects/requests/post/project.yaml",
    "projects/requests/put/single_detection_project_update_request.json": "projects/requests/put/project.yaml",
    "projects/requests/put/task_chain_project_update_request.json": "projects/requests/put/project.yaml",
    "projects/requests/put/classification_project_label_addition_request.json": "projects/requests/put/project.yaml",
    "projects/requests/put/classification_project_label_deletion_request.json": "projects/requests/put/project.yaml",
    "projects/requests/put/keypoint_detection_edit_request.json": "projects/requests/put/project.yaml",
    "projects/responses/classification_project_response.json": "projects/responses/project.yaml",
    "projects/responses/classification_label_hierarchy_project_response.json": "projects/responses/project.yaml",
    "projects/responses/segmentation_project_response.json": "projects/responses/project.yaml",
    "projects/responses/single_detection_project_response.json": "projects/responses/project.yaml",
    "projects/responses/keypoint_detection_response.json": "projects/responses/project.yaml",
    "projects/responses/task_chain_project_response.json": "projects/responses/project.yaml",
    "projects/responses/classification_project_label_addition_response.json": "projects/responses/project.yaml",
    "projects/responses/project_list_response.json": "projects/responses/project_list.yaml",
}
annotation_template_to_schema_map = {
    "annotation_template/responses/annotation_template_response.json": "annotation_template/responses/"
    "annotation_templates.yaml",
    "annotation_template/requests/annotation_template_request.json": "annotation_template/requests"
    "/annotation_template.yaml",
}
model_test_example_to_schema_map = {
    "model_test_results/responses/finished_model_test.json": "model_test_results/responses/model_test_result.yaml",
    "model_test_results/responses/running_model_test.json": "model_test_results/responses/model_test_result.yaml",
    "model_test_results/responses/model_test_result_list.json": "model_test_results/responses"
    "/model_test_result_list.yaml",
    "media_scores/requests/filter_media_scores.json": "media_scores/requests/media_score_query.yaml",
    "media_scores/responses/filtered_media_scores.json": "media_scores/responses/filtered_media_scores.yaml",
}
status_example_to_schema_map = {
    "status/responses/server_status_response.json": "status/responses/server_status.yaml",
    "status/responses/running_segmentation_response.json": "status/responses/project_status.yaml",
    "status/responses/waiting_for_classification_annotations_response.json": "status/responses/project_status.yaml",
    "status/responses/anomaly_awaiting_resource_allocation_response.json": "status/responses/project_status.yaml",
    "status/responses/incremental_learning_status_response.json": "status/responses/incremental_learning_status.yaml",
}
training_example_to_schema_map = {
    "training/requests/simple_train_request_body.json": "training/requests/train_request.yaml",
    "training/requests/advanced_train_request_body.json": "training/requests/train_request.yaml",
}
workspace_example_to_schema_map = {
    "workspaces/responses/workspace_list_response.json": "workspaces/responses/workspace_list.yaml",
}
video_prediction_example_to_schema_map = {
    "predictions/responses/video_prediction_response.json": "predictions/responses/video_prediction.yaml",
}
project_import_export_example_to_schema_map = {
    "project_import_export/requests/import_project.json": "project_import_export/requests/import_parameters.yaml",
}
PATH_TO_EXAMPLES_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../docs/rest/examples"))
base_dir = os.path.dirname(__file__) + "/../../api/schemas/"


def check_examples_with_schemas(example_to_schema_map: dict):
    """
    Checks whether an example file adheres to the rules set in a schema file.

    :param example_to_schema_map: A dictionary that contains the relative path of the
    example (from docs/rest/examples) mapped to the relative path of the schema (from
    microservices/communication/rest/schemas).
    :raises jsonschema.ValidationError if the example doesn't adhere to the schema rules
    :raises FileNotFoundError if either file is not present
    """
    for example_filename, schema_filename in example_to_schema_map.items():
        logger.info(f"Comparing {example_filename} against {schema_filename}")
        schema = RestApiValidator().load_schema_file_as_dict(base_dir + schema_filename)
        example_path = os.path.join(PATH_TO_EXAMPLES_FOLDER, example_filename)
        with open(example_path) as f:
            example = json.load(f)
        jsonschema.validate(example, schema)


class TestDocumentation:
    def test_documentation(self):
        """
        <b>Description:</b>
        Checks whether all the example files in docs/rest/examples adhere to the rules
        set by the schema files in microservices/communication/rest/schemas.

        <b>Input data:</b>
        Dictionaries that contain information on the location of the relevant
        documentation files.

        <b>Expected results:</b>
        Test passes if the example files adhere to the rules set by the schemas.

        <b>Steps</b>
        For every example_to_schema_map, which is a dictionary containing the location
        of the relevant schema for every example file, check whether the example is
        correct. For this check we use jsonschema.validate.
        """
        check_examples_with_schemas(workspace_example_to_schema_map)
        check_examples_with_schemas(annotation_example_to_schema_map)
        check_examples_with_schemas(configuration_example_to_schema_map)
        check_examples_with_schemas(dataset_example_to_schema_map)
        check_examples_with_schemas(job_example_to_schema_map)
        check_examples_with_schemas(media_example_to_schema_map)
        check_examples_with_schemas(model_example_to_schema_map)
        check_examples_with_schemas(pipeline_example_to_schema_map)
        check_examples_with_schemas(project_example_to_schema_map)
        check_examples_with_schemas(status_example_to_schema_map)
        check_examples_with_schemas(training_example_to_schema_map)
        check_examples_with_schemas(model_test_example_to_schema_map)
        check_examples_with_schemas(video_prediction_example_to_schema_map)
        check_examples_with_schemas(project_import_export_example_to_schema_map)
        check_examples_with_schemas(annotation_template_to_schema_map)
