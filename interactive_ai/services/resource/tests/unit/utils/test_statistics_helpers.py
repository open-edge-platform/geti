# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import gc
import timeit
from statistics import mean
from typing import TYPE_CHECKING
from unittest.mock import PropertyMock, call, patch

import pytest
from tests.fixtures.values import DummyValues
from tests.mock_tasks import register_detection_task
from tests.utils.test_helpers import generate_random_annotated_project

from service.label_schema_service import LabelSchemaService
from usecases.statistics import StatisticsUseCase

from geti_types import DatasetStorageIdentifier
from iai_core_py.entities.annotation_scene_state import AnnotationState
from iai_core_py.entities.evaluation_result import EvaluationPurpose
from iai_core_py.entities.label_schema import LabelSchema
from iai_core_py.entities.metrics import NullPerformance
from iai_core_py.entities.model import NullModel
from iai_core_py.entities.project import Project
from iai_core_py.entities.shapes import Ellipse, Polygon, Rectangle
from iai_core_py.entities.subset import Subset
from iai_core_py.repos import (
    AnnotationSceneRepo,
    AnnotationSceneStateRepo,
    DatasetRepo,
    EvaluationResultRepo,
    ImageRepo,
    ModelRepo,
    ModelStorageRepo,
    ProjectRepo,
    VideoRepo,
)

if TYPE_CHECKING:
    from iai_core_py.entities.annotation import Annotation


@pytest.fixture
def fxt_label_list(fxt_label):
    yield [fxt_label]


@pytest.fixture
def fxt_scored_label_list(fxt_scored_label):
    yield [fxt_scored_label]


@pytest.fixture
def fxt_image_list(fxt_image_entity):
    yield [fxt_image_entity]


@pytest.fixture
def fxt_video_list(fxt_video_entity):
    yield [fxt_video_entity]


@pytest.fixture
def fxt_n_annotations_per_shape(fxt_ann_scenes_list, fxt_label_list):
    yield len(fxt_label_list) * (len(fxt_ann_scenes_list[0].annotations) + len(fxt_ann_scenes_list[1].annotations))


@pytest.fixture
def fxt_data_stats_for_project(fxt_image_list, fxt_video_list):
    yield {
        "images": DummyValues.N_ALL_IMAGES,
        "videos": DummyValues.N_ALL_VIDEOS,
        "annotated_images": DummyValues.N_ANNOTATED_IMAGES,
        "annotated_videos": DummyValues.N_ANNOTATED_VIDEOS,
        "annotated_frames": DummyValues.N_ANNOTATED_FRAMES,
    }


@pytest.fixture
def fxt_data_stats_for_task(fxt_image_list, fxt_video_list):
    yield {
        "annotated_frames": DummyValues.N_ANNOTATED_FRAMES,
        "annotated_images": len(fxt_image_list),
        "annotated_videos": len(fxt_video_list),
    }


@pytest.fixture
def fxt_occurrence_per_label(fxt_scored_label, fxt_annotation_scene_1, fxt_n_annotations_per_shape):
    per_annotation = {fxt_scored_label.id_: 1}
    per_shape = {fxt_scored_label.id_: fxt_n_annotations_per_shape}
    yield per_annotation, per_shape


@pytest.fixture
def fxt_object_sizes(fxt_scored_label, fxt_ann_scenes_list):
    # object sizes are annotation pixel width and height used to compute size statistics
    annotations_and_media_size = []
    for ann_scene in fxt_ann_scenes_list:
        for annotation in ann_scene.annotations:
            annotations_and_media_size.append([annotation, (ann_scene.media_width, ann_scene.media_height)])
    # created per annotation-level, where each item is a Tuple[(width, height)]
    obj_sizes = []
    for annotation_and_media_size in annotations_and_media_size:
        annotation: Annotation = annotation_and_media_size[0]
        media_size: tuple[int, int] = annotation_and_media_size[1]
        shape = annotation.shape
        media_width = media_size[0]
        media_height = media_size[1]
        if isinstance(shape, Ellipse | Rectangle):
            obj_sizes.append((int(shape.width * media_width), int(shape.height * media_height)))
        elif isinstance(shape, Polygon):
            width = shape.max_x - shape.min_x
            height = shape.max_y - shape.min_y
            obj_sizes.append((int(width * media_width), int(height * media_height)))
    yield {fxt_scored_label.id_: tuple(obj_sizes)}


@pytest.fixture
def fxt_annotation_stats_for_task(fxt_label, fxt_n_annotations_per_shape, fxt_scored_label_list):
    objects_per_label = [
        {
            "id": fxt_label.id_,
            "name": fxt_label.name,
            "color": fxt_label.color.hex_str,
            "value": fxt_n_annotations_per_shape,
        }
    ]
    images_and_frames_per_label = [
        {
            "id": fxt_label.id_,
            "name": fxt_label.name,
            "color": fxt_label.color.hex_str,
            "value": len(fxt_scored_label_list),
        }
    ]
    object_size_distribution_per_label = [
        {
            "id": fxt_label.id_,
            "name": fxt_label.name,
            "color": fxt_label.color.hex_str,
            "size_distribution": tuple(DummyValues.OBJECT_SIZE_DISTRIBUTION),
            "cluster_center": DummyValues.CLUSTER_CENTER,
            "cluster_width_height": DummyValues.CLUSTER_WIDTH_HEIGHT,
            "aspect_ratio_threshold_tall": DummyValues.ASPECT_RATIO_THRESHOLD_TALL,
            "aspect_ratio_threshold_wide": DummyValues.ASPECT_RATIO_THRESHOLD_WIDE,
            "object_distribution_from_aspect_ratio": {
                "tall": DummyValues.DISTRIBUTION_TALL,
                "balanced": DummyValues.DISTRIBUTION_BALANCED,
                "wide": DummyValues.DISTRIBUTION_WIDE,
            },
        }
    ]
    yield (
        objects_per_label,
        images_and_frames_per_label,
        object_size_distribution_per_label,
    )


@pytest.fixture
def fxt_task_stats(
    fxt_label,
    fxt_model,
    fxt_image_list,
    fxt_video_list,
    fxt_n_annotations_per_shape,
    fxt_scored_label_list,
):
    yield {
        "images": DummyValues.N_ALL_IMAGES,
        "videos": DummyValues.N_ALL_VIDEOS,
        "annotated_images": DummyValues.N_ANNOTATED_IMAGES,
        "annotated_videos": DummyValues.N_ANNOTATED_VIDEOS,
        "annotated_frames": DummyValues.N_ANNOTATED_FRAMES,
        "objects_per_label": [
            {
                "id": fxt_label.id_,
                "name": fxt_label.name,
                "color": fxt_label.color.hex_str,
                "value": fxt_n_annotations_per_shape,
            }
        ],
        "images_and_frames_per_label": [
            {
                "id": fxt_label.id_,
                "name": fxt_label.name,
                "color": fxt_label.color.hex_str,
                "value": len(fxt_scored_label_list),
            }
        ],
        "object_size_distribution_per_label": [
            {
                "id": fxt_label.id_,
                "name": fxt_label.name,
                "color": fxt_label.color.hex_str,
                "size_distribution": tuple(DummyValues.OBJECT_SIZE_DISTRIBUTION),
                "cluster_center": DummyValues.CLUSTER_CENTER,
                "cluster_width_height": DummyValues.CLUSTER_WIDTH_HEIGHT,
                "aspect_ratio_threshold_tall": DummyValues.ASPECT_RATIO_THRESHOLD_TALL,
                "aspect_ratio_threshold_wide": DummyValues.ASPECT_RATIO_THRESHOLD_WIDE,
                "object_distribution_from_aspect_ratio": {
                    "tall": DummyValues.DISTRIBUTION_TALL,
                    "balanced": DummyValues.DISTRIBUTION_BALANCED,
                    "wide": DummyValues.DISTRIBUTION_WIDE,
                },
            }
        ],
    }


@pytest.fixture
def fxt_project_stats(
    fxt_label,
    fxt_model,
    fxt_trainable_task,
    fxt_image_list,
    fxt_video_list,
    fxt_n_annotations_per_shape,
):
    yield {
        "tasks": [
            {
                "task_id": fxt_trainable_task.id_,
                "objects_per_label": [
                    {
                        "id": fxt_label.id_,
                        "name": fxt_label.name,
                        "color": fxt_label.color.hex_str,
                        "value": fxt_n_annotations_per_shape,
                    }
                ],
                "object_size_distribution_per_label": [
                    {
                        "id": fxt_label.id_,
                        "name": fxt_label.name,
                        "color": fxt_label.color.hex_str,
                        "size_distribution": tuple(DummyValues.OBJECT_SIZE_DISTRIBUTION),
                        "cluster_center": DummyValues.CLUSTER_CENTER,
                        "cluster_width_height": DummyValues.CLUSTER_WIDTH_HEIGHT,
                        "aspect_ratio_threshold_tall": DummyValues.ASPECT_RATIO_THRESHOLD_TALL,
                        "aspect_ratio_threshold_wide": DummyValues.ASPECT_RATIO_THRESHOLD_WIDE,
                        "object_distribution_from_aspect_ratio": {
                            "tall": DummyValues.DISTRIBUTION_TALL,
                            "balanced": DummyValues.DISTRIBUTION_BALANCED,
                            "wide": DummyValues.DISTRIBUTION_WIDE,
                        },
                    }
                ],
                "annotated_frames": DummyValues.N_ANNOTATED_FRAMES,
                "annotated_images": len(fxt_image_list),
                "annotated_videos": len(fxt_video_list),
            }
        ],
        "overview": {
            "images": DummyValues.N_ALL_IMAGES,
            "videos": DummyValues.N_ALL_VIDEOS,
            "annotated_images": DummyValues.N_ANNOTATED_IMAGES,
            "annotated_videos": DummyValues.N_ANNOTATED_VIDEOS,
            "annotated_frames": DummyValues.N_ANNOTATED_FRAMES,
        },
    }


class TestStatisticsHelper:
    def test_get_dataset_storage_statistics_for_task(
        self,
        fxt_detection_segmentation_chain_project,
        fxt_dataset_storage,
        fxt_detection_label_schema,
        fxt_ann_scenes_list,
        fxt_data_stats_for_project,
        fxt_annotation_stats_for_task,
        fxt_model,
        fxt_task_stats,
        fxt_detection_task,
    ) -> None:
        with (
            patch.object(AnnotationSceneRepo, "__init__", lambda _self, _dataset_storage: None),
            patch.object(
                StatisticsUseCase,
                "get_data_stats_for_dataset_storage",
                return_value=fxt_data_stats_for_project,
            ) as mock_get_data_stats_for_project,
            patch.object(
                StatisticsUseCase,
                "get_annotation_stats_for_task",
                return_value=fxt_annotation_stats_for_task,
            ) as mock_get_annotation_stats_for_task,
            patch.object(Project, "tasks", new_callable=PropertyMock) as mock_task_list,
            patch.object(
                LabelSchemaService,
                "get_latest_label_schema_for_task",
                return_value=fxt_detection_label_schema,
            ),
        ):
            mock_task_list.return_value = [fxt_detection_task]

            result = StatisticsUseCase.get_dataset_storage_statistics_for_task(
                project=fxt_detection_segmentation_chain_project,
                dataset_storage=fxt_dataset_storage,
                task_id=fxt_detection_task.id_,
            )

            assert result == fxt_task_stats
            mock_get_data_stats_for_project.assert_called_once_with(
                project=fxt_detection_segmentation_chain_project,
                dataset_storage=fxt_dataset_storage,
                task_id=fxt_detection_task.id_,
            )
            mock_get_annotation_stats_for_task.assert_called_once_with(
                task_node_label_schema=fxt_detection_label_schema,
                dataset_storage_identifier=fxt_dataset_storage.identifier,
            )

    def test_get_dataset_storage_statistics(
        self,
        fxt_project,
        fxt_dataset_storage,
        fxt_detection_label_schema,
        fxt_ann_scenes_list,
        fxt_data_stats_for_project,
        fxt_annotation_stats_for_task,
        fxt_data_stats_for_task,
        fxt_optimized_model,
        fxt_project_stats,
        fxt_trainable_task,
    ) -> None:
        with (
            patch.object(AnnotationSceneRepo, "__init__", lambda _self, _dataset_storage: None),
            patch.object(
                StatisticsUseCase,
                "get_data_stats_for_dataset_storage",
                return_value=fxt_data_stats_for_project,
            ) as mock_get_data_stats_for_project,
            patch.object(
                StatisticsUseCase,
                "get_annotation_stats_for_task",
                return_value=fxt_annotation_stats_for_task,
            ) as mock_get_annotation_stats_for_task,
            patch.object(
                StatisticsUseCase,
                "get_data_stats_for_task",
                return_value=fxt_data_stats_for_task,
            ) as mock_get_data_stats_for_task,
            patch.object(Project, "tasks", new_callable=PropertyMock) as mock_task_list,
            patch.object(
                LabelSchemaService,
                "get_latest_label_schema_for_task",
                return_value=fxt_detection_label_schema,
            ),
            patch.object(
                ModelRepo,
                "get_all_equivalent_model_ids",
                return_value=[fxt_optimized_model.id_],
            ),
        ):
            mock_task_list.return_value = [fxt_trainable_task]

            result = StatisticsUseCase.get_dataset_storage_statistics(
                project=fxt_project, dataset_storage=fxt_dataset_storage
            )

            assert result == fxt_project_stats
            mock_get_data_stats_for_project.assert_called_once_with(
                project=fxt_project,
                dataset_storage=fxt_dataset_storage,
            )
            mock_get_annotation_stats_for_task.assert_called()
            mock_get_data_stats_for_task.assert_called()

    def test_get_annotation_stats_for_task(
        self,
        request,
        fxt_detection_task,
        fxt_detection_label_schema,
        fxt_ann_scenes_list,
        fxt_annotation_stats_for_task,
        fxt_scored_label_list,
        fxt_label,
        fxt_dataset_storage,
        fxt_occurrence_per_label,
        fxt_object_sizes,
    ) -> None:
        with (
            patch.object(LabelSchema, "get_labels", return_value=[fxt_label]) as mock_schema_get_labels,
            patch.object(
                AnnotationSceneRepo,
                "get_annotation_count_and_object_sizes",
                return_value=(
                    fxt_object_sizes,
                    fxt_occurrence_per_label[0],
                    fxt_occurrence_per_label[1],
                ),
            ) as mock_get_annotation_object_sizes,
        ):
            result = StatisticsUseCase.get_annotation_stats_for_task(
                task_node_label_schema=fxt_detection_label_schema,
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                include_empty=False,
            )

            mock_schema_get_labels.assert_called()
            mock_get_annotation_object_sizes.assert_called()
            assert result == fxt_annotation_stats_for_task

    def test_get_data_stats_for_project(
        self,
        mock_image_repo,
        mock_video_repo,
        fxt_project,
        fxt_dataset_storage,
        fxt_ann_scenes_list,
        fxt_states_by_annotation_scene,
        fxt_data_stats_for_project,
    ) -> None:
        with (
            patch.object(
                AnnotationSceneStateRepo,
                "count_images_state_for_task",
                return_value=DummyValues.N_ANNOTATED_IMAGES,
            ) as mock_count_images,
            patch.object(
                AnnotationSceneStateRepo,
                "count_video_frames_state_for_task",
                return_value=DummyValues.N_ANNOTATED_FRAMES,
            ) as mock_count_video_frames,
            patch.object(
                AnnotationSceneStateRepo,
                "count_videos_state_for_task",
                return_value=DummyValues.N_ANNOTATED_VIDEOS,
            ) as mock_count_videos,
            patch.object(ImageRepo, "count", return_value=DummyValues.N_ALL_IMAGES) as mock_count_all_images,
            patch.object(VideoRepo, "count", return_value=DummyValues.N_ALL_VIDEOS) as mock_count_all_videos,
        ):
            result = StatisticsUseCase.get_data_stats_for_dataset_storage(
                project=fxt_project,
                dataset_storage=fxt_dataset_storage,
            )

            assert result == fxt_data_stats_for_project
            mock_count_all_images.assert_called_once_with()
            mock_count_all_videos.assert_called_once_with()
            mock_count_images.assert_called_once()
            mock_count_videos.assert_called_once()
            mock_count_video_frames.assert_called()

    def test_get_data_stats_for_task(
        self,
        fxt_project,
        fxt_dataset_storage,
        fxt_detection_task,
        fxt_mongo_id,
        fxt_video_entity,
        fxt_image_entity,
        fxt_data_stats_for_task,
    ) -> None:
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            dataset_storage_id=fxt_dataset_storage.id_,
        )
        annotations_states = [
            AnnotationState.ANNOTATED,
            AnnotationState.PARTIALLY_ANNOTATED,
        ]
        task_id = fxt_detection_task.id_

        with (
            patch.object(
                AnnotationSceneStateRepo,
                "__init__",
                lambda _self, _dataset_storage: None,
            ),
            patch.object(
                AnnotationSceneStateRepo,
                "count_video_frames_state_for_task",
                return_value=fxt_data_stats_for_task["annotated_frames"],
            ) as mock_count_annotated_frames,
            patch.object(
                AnnotationSceneStateRepo,
                "count_images_state_for_task",
                return_value=fxt_data_stats_for_task["annotated_images"],
            ) as mock_count_annotated_images,
            patch.object(
                AnnotationSceneStateRepo,
                "count_videos_state_for_task",
                return_value=fxt_data_stats_for_task["annotated_videos"],
            ) as mock_count_annotated_videos,
        ):
            result = StatisticsUseCase.get_data_stats_for_task(
                task_id=task_id,
                dataset_storage_identifier=dataset_storage_identifier,
            )

            assert result == fxt_data_stats_for_task

            mock_count_annotated_frames.assert_called_once_with(
                annotation_states=annotations_states,
                task_id=task_id,
            )
            mock_count_annotated_images.assert_called_once_with(
                annotation_states=annotations_states,
                task_id=task_id,
            )
            mock_count_annotated_videos.assert_called_once_with(
                annotation_states=annotations_states,
                task_id=task_id,
            )

    @pytest.mark.parametrize("fxt_filled_image_dataset_storage", [25], indirect=True)
    def test_get_dataset_statistics(self, fxt_filled_image_dataset_storage) -> None:
        """
        Tests the dataset statistics on a dataset containing 25 images
        """
        dataset_repo = DatasetRepo(fxt_filled_image_dataset_storage.identifier)
        dataset = dataset_repo.get_by_id(fxt_filled_image_dataset_storage.id_)
        expected_stats_dict = {
            "id": dataset.id_,
            "subset_info": {
                "training": len(dataset.get_subset(Subset.TRAINING)),
                "testing": len(dataset.get_subset(Subset.TESTING)),
                "validation": len(dataset.get_subset(Subset.VALIDATION)),
            },
            "dataset_info": {
                "videos": 0,
                "frames": 0,
                "images": len(dataset),
            },
            "creation_time": str(dataset.creation_date),
        }

        stats = StatisticsUseCase.get_dataset_statistics(
            dataset_storage=fxt_filled_image_dataset_storage, dataset=dataset
        )

        assert expected_stats_dict == stats

    def test_get_model_statistics(
        self,
        fxt_db_project_service,
        fxt_evaluation_result,
        fxt_training_performance,
    ) -> None:
        project = fxt_db_project_service.create_annotated_detection_classification_project()
        model = fxt_db_project_service.create_and_save_model()
        model.performance = fxt_training_performance
        eq_model_ids = ModelRepo(model.model_storage_identifier).get_all_equivalent_model_ids(model)
        metrics_names = {"Training date", "Training job duration", "Dataset split"}

        with patch.object(
            EvaluationResultRepo,
            "get_latest_by_model_ids",
            return_value=fxt_evaluation_result,
        ) as mock_get_latest_result:
            result = StatisticsUseCase.get_model_statistics(
                model=model,
                project_identifier=project.identifier,
            )

        mock_get_latest_result.assert_has_calls(
            [
                call(
                    equivalent_model_ids=eq_model_ids,
                    purpose=EvaluationPurpose.VALIDATION,
                ),
                call(equivalent_model_ids=eq_model_ids, purpose=EvaluationPurpose.TEST),
            ]
        )
        for metrics_group in model.performance.dashboard_metrics:
            assert metrics_group in result.charts
        result_metrics_names = {m.visualization_info.name for m in result.charts}
        assert metrics_names.issubset(result_metrics_names)

    @pytest.mark.skip(reason="Slow test, only run when needed to test performance.")
    def test_model_statistics_performance(self, fxt_db_project_service) -> None:
        n_dataset_items = 100_000
        # Create project with 2 labels
        project = fxt_db_project_service.create_annotated_detection_classification_project(
            num_images_per_label=(n_dataset_items // 2)
        )
        model = fxt_db_project_service.create_and_save_model()

        project_id = project.id_
        model_storage_id = model.model_storage.id_
        model_id = model.id_

        # Avoid misleading results by removing project and model instances from memory
        del project
        del model
        gc.collect()

        project = ProjectRepo().get_by_id(project_id)
        model_storage = ModelStorageRepo(project.identifier).get_by_id(model_storage_id)
        model = ModelRepo(model_storage.identifier).get_by_id(model_id)

        def fn_model_stats():
            StatisticsUseCase.get_model_statistics(
                model=model,
                project_identifier=project.identifier,
            )

        # Benchmark run time on 5 calls
        run_time = timeit.repeat(stmt=fn_model_stats, repeat=5, number=1)

        time_limit = 1.0  # in seconds
        assert mean(run_time) < time_limit
        assert max(run_time) < time_limit

    @pytest.mark.skip(reason="Slow test, only run when needed to test performance.")
    def test_statistics_performance(self, request) -> None:
        n_annotations = 50_000

        model_template = register_detection_task(request)
        project = generate_random_annotated_project(
            test_case=request,
            name="__Test status 1",
            description="TestTaskChain()",
            model_template_id=model_template,
            number_of_images=n_annotations,
            number_of_videos=0,
        )[0]

        def fn_statistics():
            StatisticsUseCase.get_dataset_statistics(project, project.get_training_dataset_storage())

        # Benchmark run time on 5 calls
        run_time = timeit.repeat(stmt=fn_statistics, repeat=5, number=1)

        time_limit = 10.0  # in seconds
        assert mean(run_time) < time_limit
        assert max(run_time) < time_limit

    def test_get_model_performance_null_model(self, fxt_project) -> None:
        # Act
        with (
            patch.object(
                EvaluationResultRepo,
                "get_performance_by_model_ids",
            ) as mock_get_performance,
            patch.object(
                ModelRepo,
                "get_all_equivalent_model_ids",
            ) as mock_get_equivalent_model_ids,
        ):
            result = StatisticsUseCase.get_model_performance(
                model=NullModel(),
                project_identifier=fxt_project.identifier,
            )

        # Assert
        assert result == NullPerformance()
        mock_get_equivalent_model_ids.assert_not_called()
        mock_get_performance.assert_not_called()
