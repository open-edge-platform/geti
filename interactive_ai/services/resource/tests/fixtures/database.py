# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

# type: ignore

import copy
import logging
import os
import tempfile
from collections.abc import Generator, Sequence
from unittest.mock import patch

import cv2
import numpy as np
import pytest

from communication.rest_parsers import RestProjectParser
from service.label_schema_service import LabelSchemaService

from geti_types import CTX_SESSION_VAR, ID, DatasetStorageIdentifier, ImageIdentifier, MediaType, ProjectIdentifier
from sc_sdk.adapters.binary_interpreters import NumpyBinaryInterpreter
from sc_sdk.algorithms import ModelTemplateList
from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters
from sc_sdk.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.dataset_storage import DatasetStorage
from sc_sdk.entities.datasets import Dataset, DatasetPurpose
from sc_sdk.entities.image import Image
from sc_sdk.entities.label import Label
from sc_sdk.entities.label_schema import LabelSchema
from sc_sdk.entities.media import ImageExtensions, MediaPreprocessing, MediaPreprocessingStatus, VideoExtensions
from sc_sdk.entities.metrics import Performance, ScoreMetric
from sc_sdk.entities.model import (
    Model,
    ModelConfiguration,
    ModelOptimizationType,
    ModelPrecision,
    ModelStatus,
    TrainingFramework,
)
from sc_sdk.entities.model_storage import ModelStorage
from sc_sdk.entities.model_template import HyperParameterData, InstantiationType, ModelTemplate, TaskFamily, TaskType
from sc_sdk.entities.project import Project
from sc_sdk.entities.scored_label import ScoredLabel
from sc_sdk.entities.shapes import Rectangle
from sc_sdk.entities.subset import Subset
from sc_sdk.entities.task_node import TaskNode
from sc_sdk.entities.video import Video
from sc_sdk.repos import (
    AnnotationSceneRepo,
    AnnotationSceneStateRepo,
    ConfigurableParametersRepo,
    DatasetRepo,
    ImageRepo,
    LabelSchemaRepo,
    ModelRepo,
    VideoRepo,
)
from sc_sdk.repos.dataset_entity_repo import PipelineDatasetRepo
from sc_sdk.repos.storage.binary_repos import ImageBinaryRepo
from sc_sdk.services import ModelService
from sc_sdk.services.dataset_storage_filter_service import DatasetStorageFilterService
from sc_sdk.utils.annotation_scene_state_helper import AnnotationSceneStateHelper
from sc_sdk.utils.deletion_helpers import DeletionHelpers
from sc_sdk.utils.project_builder import PersistedProjectBuilder, ProjectBuilder

logger = logging.getLogger(__name__)


DETECTION_PIPELINE_DATA = {
    "connections": [
        {
            "from": "dataset",
            "to": "detection task",
        },
    ],
    "tasks": [
        {"task_type": "dataset", "title": "dataset"},
        {
            "task_type": "detection",
            "title": "detection task",
            "labels": [
                {
                    "color": "#0015FFFF",
                    "group": "default_detection",
                    "hotkey": "ctrl+5",
                    "name": "object",
                },
            ],
        },
    ],
}


DETECTION_CLASSIFICATION_PIPELINE_DATA = {
    "connections": [
        {
            "from": "dataset",
            "to": "detection task",
        },
        {
            "from": "detection task",
            "to": "crop task",
        },
        {
            "from": "crop task",
            "to": "classification task",
        },
    ],
    "tasks": [
        {
            "task_type": "dataset",
            "title": "dataset",
        },
        {
            "task_type": "detection",
            "title": "detection task",
            "labels": [
                {
                    "color": "#0015FFFF",
                    "group": "default_detection",
                    "hotkey": "ctrl+5",
                    "name": "object",
                },
            ],
        },
        {"task_type": "crop", "title": "crop task"},
        {
            "task_type": "classification",
            "title": "classification task",
            "labels": [
                {
                    "color": "#0015FFFF",
                    "group": "default_classification",
                    "hotkey": "ctrl+6",
                    "name": "rectangle",
                },
                {
                    "color": "#7F000AFF",
                    "group": "default_classification",
                    "hotkey": "ctrl+7",
                    "name": "circle",
                },
            ],
        },
    ],
}


ANOMALY_CLASSIFICATION_PIPELINE_DATA = {
    "connections": [
        {
            "from": "dataset",
            "to": "anomaly classification task",
        },
    ],
    "tasks": [
        {
            "task_type": "dataset",
            "title": "dataset",
        },
        {
            "task_type": "anomaly_classification",
            "title": "anomaly classification task",
        },
    ],
}


class DBProjectService:
    def __init__(self) -> None:
        self._num_images_per_label = 12
        self._height = 40
        self._width = 50
        self._rng = np.random.default_rng(0)
        self._workspace_id = CTX_SESSION_VAR.get().workspace_id
        self._project: Project | None = None
        self._dataset_storage: DatasetStorage | None = None
        self._dataset_items: list[DatasetItem] = []
        self._dataset: Dataset | None = None
        self._label_schema: LabelSchema | None = None
        self._task_node_1: TaskNode | None = None
        self._model_storage_1: ModelStorage | None = None
        self._label_schema_1: LabelSchema | None = None
        self._task_node_2: TaskNode | None = None
        self._model_storage_2: ModelStorage | None = None
        self._label_schema_2: LabelSchema | None = None

    @property
    def workspace_id(self) -> ID:
        return self._workspace_id

    @property
    def project(self) -> Project:
        if self._project is None:
            raise RuntimeError("Project has not been created yet. Call one of the self.create_*_project first.")
        return self._project

    @property
    def project_identifier(self) -> ProjectIdentifier:
        return self.project.identifier

    @property
    def dataset_storage(self) -> DatasetStorage:
        if self._dataset_storage is None:
            self._dataset_storage = self.project.get_training_dataset_storage()
        return self._dataset_storage

    @property
    def dataset_storage_identifier(self) -> DatasetStorageIdentifier:
        return DatasetStorageIdentifier(
            workspace_id=self.workspace_id,
            project_id=self.project.id_,
            dataset_storage_id=self.dataset_storage.id_,
        )

    @property
    def training_dataset(self) -> Dataset:
        if self._dataset is None:
            self._dataset = Dataset(
                items=self._dataset_items,
                purpose=DatasetPurpose.TRAINING,
                label_schema_id=self.label_schema_1.id_,
                id=DatasetRepo.generate_id(),
            )
            DatasetRepo(self.dataset_storage.identifier).save(self._dataset)
        return self._dataset

    @property
    def dataset(self) -> Dataset:
        return self.training_dataset

    @property
    def label_schema(self) -> LabelSchema:
        if self._label_schema is None:
            self._label_schema = LabelSchemaRepo(self.project_identifier).get_latest()
        return self._label_schema

    @property
    def task_node_1(self) -> TaskNode:
        if self._task_node_1 is None:
            self._task_node_1 = self.project.get_trainable_task_nodes()[0]
        return self._task_node_1

    @property
    def model_storage_1(self) -> ModelStorage:
        if self._model_storage_1 is None:
            self._model_storage_1 = ModelService.get_active_model_storage(
                self.project_identifier,
                task_node_id=self.task_node_1.id_,
            )
        return self._model_storage_1

    @property
    def label_schema_1(self) -> LabelSchema:
        if self._label_schema_1 is None:
            self._label_schema_1 = LabelSchemaService.get_latest_label_schema_for_task(
                project_identifier=self.project.identifier,
                task_node_id=self.task_node_1.id_,
            )
        return self._label_schema_1

    @property
    def task_node_2(self) -> TaskNode:
        if self._task_node_2 is None:
            self._task_node_2 = self.project.get_trainable_task_nodes()[1]
        return self._task_node_2

    @property
    def model_storage_2(self) -> ModelStorage:
        if self._model_storage_2 is None:
            self._model_storage_2 = ModelService.get_active_model_storage(
                project_identifier=self.project_identifier,
                task_node_id=self.task_node_2.id_,
            )
        return self._model_storage_2

    @property
    def label_schema_2(self) -> LabelSchema:
        if self._label_schema_2 is None:
            self._label_schema_2 = LabelSchemaService.get_latest_label_schema_for_task(
                project_identifier=self.project.identifier,
                task_node_id=self.task_node_2.id_,
            )
        return self._label_schema_2

    def reload_label_schema(self) -> None:
        self._label_schema = None
        self._label_schema_1 = None
        self._label_schema_2 = None

    def create_and_save_model(
        self,
        task_node_index: int = 0,
        model_status: ModelStatus = ModelStatus.SUCCESS,
        hyper_parameters: ConfigurableParameters = None,
        dataset: Dataset | None = None,
        training_framework: TrainingFramework | None = None,
    ) -> Model:
        if task_node_index == 0:
            model_storage = self.model_storage_1
            label_schema = self.label_schema_1
        else:
            model_storage = self.model_storage_2
            label_schema = self.label_schema_2

        if hyper_parameters is None:
            hyper_parameters = ConfigurableParametersRepo(
                project_identifier=self.project.identifier
            ).get_or_create_hyper_parameters(model_storage=model_storage)
        configuration = ModelConfiguration(
            configurable_parameters=hyper_parameters,
            label_schema=label_schema,
        )

        if dataset is None:
            dataset = self.dataset
        else:
            dataset.dataset_storage = self.dataset_storage
            dataset_repo = DatasetRepo(self.dataset_storage.identifier)
            dataset_repo.save_shallow(instance=dataset)

        base_model = Model(
            project=self.project,
            model_storage=model_storage,
            train_dataset=dataset,
            configuration=configuration,
            id_=ModelRepo.generate_id(),
            performance=Performance(score=ScoreMetric(value=0.8, name="accuracy")),
            data_source_dict={"dummy.file": b"DUMMY_DATA"},
            model_status=model_status,
            has_xai_head=True,
            optimization_type=ModelOptimizationType.NONE,
            training_framework=training_framework,
        )
        mo_model = Model(
            project=self.project,
            model_storage=model_storage,
            train_dataset=dataset,
            configuration=configuration,
            id_=ModelRepo.generate_id(),
            performance=Performance(score=ScoreMetric(value=0.8, name="accuracy")),
            previous_trained_revision=base_model,
            data_source_dict={"dummy.file": b"DUMMY_DATA"},
            model_status=model_status,
            has_xai_head=True,
            precision=[ModelPrecision.FP32],
            optimization_type=ModelOptimizationType.MO,
            training_framework=training_framework,
        )
        model_repo = ModelRepo(model_storage.identifier)
        model_repo.save_many([base_model, mo_model])

        return base_model

    @staticmethod
    def create_detection_model_templates() -> list[ModelTemplate]:
        model_template_dataset = ModelTemplateList().get_by_id("dataset")
        hyper_parameters = HyperParameterData(base_path="")
        model_template_detection = ModelTemplate(
            model_template_id="detection",
            model_template_path="",
            name="mock_detection",
            task_type=TaskType.DETECTION,
            task_family=TaskFamily.VISION,
            instantiation=InstantiationType.NONE,
            hyper_parameters=hyper_parameters,
            capabilities=["compute_representations"],
            is_default_for_task=True,
        )
        ModelTemplateList().register_model_template(model_template_detection)
        return [
            model_template_dataset,
            model_template_detection,
        ]

    @staticmethod
    def create_detection_classification_model_templates() -> list[ModelTemplate]:
        model_template_dataset = ModelTemplateList().get_by_id("dataset")
        hyper_parameters = HyperParameterData(base_path="")
        model_template_detection = ModelTemplate(
            model_template_id="detection",
            model_template_path="",
            name="mock_detection",
            task_type=TaskType.DETECTION,
            task_family=TaskFamily.VISION,
            instantiation=InstantiationType.NONE,
            hyper_parameters=hyper_parameters,
            capabilities=["compute_representations"],
            is_default_for_task=True,
        )
        ModelTemplateList().register_model_template(model_template_detection)
        model_template_crop = ModelTemplateList().get_by_id("crop")
        model_template_classification = ModelTemplate(
            model_template_id="classification",
            model_template_path="",
            name="mock_classification",
            task_type=TaskType.CLASSIFICATION,
            task_family=TaskFamily.VISION,
            instantiation=InstantiationType.NONE,
            hyper_parameters=hyper_parameters,
            capabilities=["compute_representations"],
            is_default_for_task=True,
        )
        ModelTemplateList().register_model_template(model_template_classification)
        return [
            model_template_dataset,
            model_template_detection,
            model_template_crop,
            model_template_classification,
        ]

    @staticmethod
    def create_anomaly_classification_model_templates() -> list[ModelTemplate]:
        model_template_dataset = ModelTemplateList().get_by_id("dataset")
        model_template_classification = ModelTemplateList().get_by_id("anomaly_classification")
        return [
            model_template_dataset,
            model_template_classification,
        ]

    def create_empty_project(
        self,
        name="test detection project",
        pipeline_data=None,
        model_templates=None,
    ) -> Project:
        # We are patching as "model_template_id" is no longer allowed in the request
        # body for project creation. The values from DEFAULT_MODEL_TEMPLATES such as
        # "Custom_Object_Detection_Gen3_ATSS" are not registered model_templates during
        # testing. SCPipelineFactory._get_model_template_from_task_data() is trying to
        # get this with ModelTemplateList().get_by_id(model_template_id), but cannot.
        # TODO CVS-94495
        if (pipeline_data is None) ^ (model_templates is None):
            raise Exception("Please provide both or none, not one.")
        if pipeline_data is None or model_templates is None:
            pipeline_data = copy.deepcopy(DETECTION_PIPELINE_DATA)
            model_templates = self.create_detection_model_templates()
        parser_kwargs = {"rest_data": {"name": name, "pipeline": pipeline_data}}
        with patch.object(
            ProjectBuilder,
            "get_default_model_template_by_task_type",
            side_effect=model_templates,
        ):
            self._project, _, _ = PersistedProjectBuilder.build_full_project(
                creator_id="",
                parser_class=RestProjectParser,
                parser_kwargs=parser_kwargs,
            )

        return self._project

    def create_annotated_detection_project(self, num_images_per_label: int = 12) -> Project:
        model_templates = self.create_detection_model_templates()
        project = self.create_empty_project(
            name="test annotated detection project",
            pipeline_data=DETECTION_PIPELINE_DATA,
            model_templates=model_templates,
        )

        self._num_images_per_label = num_images_per_label
        labels = self.label_schema_1.get_labels(include_empty=False)
        self._generate_randomly_annotated_images(detection_labels=labels)

        return project

    def create_annotated_detection_classification_project(self, num_images_per_label: int = 6) -> Project:
        model_templates = self.create_detection_classification_model_templates()
        project = self.create_empty_project(
            name="test annotated detection classification project",
            pipeline_data=DETECTION_CLASSIFICATION_PIPELINE_DATA,  # type: ignore
            model_templates=model_templates,
        )

        self._num_images_per_label = num_images_per_label
        detection_labels = self.label_schema_1.get_labels(include_empty=False)
        classification_labels = self.label_schema_2.get_labels(include_empty=False)
        self._generate_randomly_annotated_images(
            detection_labels=detection_labels,
            classification_labels=classification_labels,
        )

        return project

    def _generate_randomly_annotated_images(
        self, detection_labels: list[Label], classification_labels: list[Label] | None = None
    ):
        if classification_labels is None:
            classification_labels = []
        if classification_labels:
            label_lists = [
                [det_label, cls_label] for det_label in detection_labels for cls_label in classification_labels
            ]
        else:
            label_lists = [[det_label] for det_label in detection_labels]

        div, rem = divmod(self._num_images_per_label, 3)
        subsets = [Subset.TRAINING] * rem + [
            Subset.TRAINING,
            Subset.VALIDATION,
            Subset.TESTING,
        ] * div

        # Generate randomly annotated images and a train dataset
        for labels in label_lists:
            images = [
                self.create_and_save_random_image(name=f"image_{labels[-1].name}_{i}")
                for i in range(self._num_images_per_label)
            ]
            annotation_scenes = [
                self.create_and_save_random_annotation_scene(
                    image=image,
                    labels=labels,
                )
                for image in images
            ]
            self._dataset_items += [
                DatasetItem(
                    media=images[i],
                    annotation_scene=annotation_scenes[i],
                    subset=subsets[i],
                    id_=DatasetRepo.generate_id(),
                )
                for i in range(self._num_images_per_label)
            ]

    def create_and_save_random_image(self, name: str) -> Image:
        # Generate random image content
        np_image = self._rng.integers(low=0, high=255, size=(self._height, self._width, 3), dtype=np.uint8)
        # Create and save Image
        image_id = ImageRepo.generate_id()
        extension = ImageExtensions.PNG
        filename = f"{str(image_id)}{extension.value}"
        image_binary_repo = ImageBinaryRepo(self.dataset_storage.identifier)
        binary_filename = image_binary_repo.save(
            dst_file_name=filename,
            data_source=NumpyBinaryInterpreter.get_bytes_from_numpy(image_numpy=np_image, extension=extension.value),
        )
        size = image_binary_repo.get_object_size(binary_filename)
        image = Image(
            name=name,
            uploader_id="",
            id=image_id,
            width=self._width,
            height=self._height,
            size=size,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
        ImageRepo(self.dataset_storage.identifier).save(instance=image)
        DatasetStorageFilterService.on_new_media_upload(
            workspace_id=self.workspace_id,
            project_id=self.project.id_,
            dataset_storage_id=self.dataset_storage_identifier.dataset_storage_id,
            media_id=image.id_,
            media_type=MediaType.IMAGE,
        )
        return image

    def get_pipeline_dataset(self):
        return PipelineDatasetRepo.get_or_create(self.dataset_storage_identifier)

    def create_and_save_random_video(self, name: str, number_of_frames: int = 30) -> Video:
        video_repo = VideoRepo(self.dataset_storage_identifier)
        # create a video path using video id and extension
        video_id = video_repo.generate_id()
        video_path = os.path.join(tempfile.gettempdir(), f"{video_id}.mp4")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps = 30.0
        video_writer = cv2.VideoWriter(video_path, fourcc, fps, (self._width, self._height))
        for _ in range(number_of_frames):
            img = self._rng.integers(low=0, high=255, size=(self._height, self._width, 3), dtype=np.uint8)
            video_writer.write(img)
        video_writer.release()

        filename = video_repo.binary_repo.save(dst_file_name=video_path, data_source=video_path)
        size = video_repo.binary_repo.get_object_size(filename)

        if os.path.exists(video_path):
            os.remove(video_path)

        _, extension = os.path.splitext(filename)

        try:
            video_extension = VideoExtensions[extension[1:].upper()]
        except KeyError:
            video_extension = VideoExtensions.MP4

        video = Video(
            name=name,
            stride=1,
            id=video_id,
            uploader_id="",
            extension=video_extension,
            fps=fps,
            width=self._width,
            height=self._height,
            total_frames=number_of_frames,
            size=size,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
        video_repo.save(video)

        return video

    def create_and_save_random_annotation_scene(
        self,
        image: Image,
        labels: Sequence[Label],
        full_size_rectangle: bool = False,
        n_annotations: int = 1,
    ) -> AnnotationScene:
        annotations = []
        for _i in range(n_annotations):
            if full_size_rectangle:
                x1, x2, y1, y2 = 0, 1, 0, 1
            else:
                values = self._rng.uniform(size=4)
                x1 = values[0]
                x2 = min(x1 + values[1], 1)
                y1 = values[2]
                y2 = min(y1 + values[3], 1)

            annotation = Annotation(
                shape=Rectangle(x1=x1, x2=x2, y1=y1, y2=y2),
                labels=[ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=1.0) for label in labels],
            )
            annotations.append(annotation)

        annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=ImageIdentifier(image.id_),
            media_height=image.height,
            media_width=image.width,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=annotations,
        )
        return self.save_annotation_scene_and_state(annotation_scene=annotation_scene)

    def save_annotation_scene_and_state(self, annotation_scene: AnnotationScene) -> AnnotationScene:
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=self.workspace_id,
            project_id=self.project.id_,
            dataset_storage_id=self.dataset_storage.id_,
        )
        ann_scene_repo = AnnotationSceneRepo(dataset_storage_identifier)
        ann_scene_state_repo = AnnotationSceneStateRepo(dataset_storage_identifier)
        ann_scene_repo.save(annotation_scene)
        annotation_scene_state = AnnotationSceneStateHelper.compute_annotation_scene_state(
            annotation_scene=annotation_scene,
            project=self.project,
            labels_to_revisit_per_annotation={},
            labels_to_revisit_full_scene=[],
        )
        ann_scene_state_repo.save(annotation_scene_state)
        DatasetStorageFilterService.on_new_annotation_scene(
            project_id=self.project.id_,
            dataset_storage_id=dataset_storage_identifier.dataset_storage_id,
            annotation_scene_id=annotation_scene.id_,
        )
        return annotation_scene

    def cleanup(self) -> None:
        DeletionHelpers.delete_project_by_id(project_id=self.project.id_)


@pytest.fixture
def fxt_db_project_service() -> Generator[DBProjectService, None, None]:
    db_project_service = DBProjectService()

    yield db_project_service

    db_project_service.cleanup()
