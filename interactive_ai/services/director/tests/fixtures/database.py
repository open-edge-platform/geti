# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

# type: ignore

import copy
import logging
import os
import tempfile
from collections.abc import Generator, Sequence
from dataclasses import dataclass, fields
from enum import Enum
from functools import lru_cache
from typing import Any
from unittest.mock import patch

import cv2
import jsonschema
import numpy as np
import pytest

from coordination.configuration_manager.task_node_config import TaskNodeConfig

from geti_fastapi_tools.validation import RestApiValidator
from geti_types import CTX_SESSION_VAR, ID, DatasetStorageIdentifier, ImageIdentifier, MediaType, ProjectIdentifier
from iai_core.adapters.binary_interpreters import NumpyBinaryInterpreter
from iai_core.algorithms import ModelTemplateList
from iai_core.configuration.elements.component_parameters import ComponentParameters, ComponentType
from iai_core.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.datasets import Dataset, DatasetPurpose
from iai_core.entities.image import Image
from iai_core.entities.label import Domain, Label
from iai_core.entities.label_schema import LabelSchema
from iai_core.entities.media import ImageExtensions, MediaPreprocessing, MediaPreprocessingStatus, VideoExtensions
from iai_core.entities.metrics import Performance, ScoreMetric
from iai_core.entities.model import (
    Model,
    ModelConfiguration,
    ModelOptimizationType,
    ModelPrecision,
    ModelStatus,
    TrainingFramework,
)
from iai_core.entities.model_storage import ModelStorage
from iai_core.entities.model_template import HyperParameterData, InstantiationType, ModelTemplate, TaskFamily, TaskType
from iai_core.entities.project import Project
from iai_core.entities.scored_label import ScoredLabel
from iai_core.entities.shapes import Rectangle
from iai_core.entities.subset import Subset
from iai_core.entities.task_node import TaskNode
from iai_core.entities.video import Video
from iai_core.factories import ProjectParser, ProjectParserInternalError, ProjectUpdateParser
from iai_core.repos import (
    AnnotationSceneRepo,
    AnnotationSceneStateRepo,
    ConfigurableParametersRepo,
    DatasetRepo,
    ImageRepo,
    LabelSchemaRepo,
    ModelRepo,
    VideoRepo,
)
from iai_core.repos.dataset_entity_repo import PipelineDatasetRepo
from iai_core.repos.storage.binary_repos import ImageBinaryRepo
from iai_core.services import ModelService
from iai_core.services.dataset_storage_filter_service import DatasetStorageFilterService
from iai_core.utils.annotation_scene_state_helper import AnnotationSceneStateHelper
from iai_core.utils.deletion_helpers import DeletionHelpers
from iai_core.utils.project_builder import PersistedProjectBuilder, ProjectBuilder

__all__ = [
    "DETECTION_CLASSIFICATION_PIPELINE_DATA",
    "RestProjectParser",
    "RestProjectUpdateParser",
]

logger = logging.getLogger(__name__)


COLOR = "color"
CONNECTIONS = "connections"
FROM = "from"
GROUP = "group"
HOTKEY = "hotkey"
ID_ = "id"
IS_DELETED = "is_deleted"
IS_EMPTY = "is_empty"
LABELS = "labels"
NAME = "name"
PARENT_ID = "parent_id"
PIPELINE = "pipeline"
REVISIT_AFFECTED_ANNOTATIONS = "revisit_affected_annotations"
TASK_TYPE = "task_type"
TASKS = "tasks"
TITLE = "title"
TO = "to"
EDGES = "edges"
LABEL = "label"
KEYPOINT_STRUCTURE = "keypoint_structure"
NODES = "nodes"
POSITIONS = "positions"


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


class OperationType(Enum):
    """
    This Enum represents a type of operation that can be performed on a project
    """

    CREATE = "create"
    UPDATE = "update"


@dataclass
class LabelProperties:
    """
    Class representing those properties of a label (inferred from its REST
    representation) that are subject to additional data validation

    :var name: Name of the label
    :var task_title: Title of the task to which the label belongs
    :var domain: Domain to which the label applies
    :var color: Color of the label
    :var id_: Unique database ID of the label
    :var group: Name of the label group to which the label belongs
    :var is_empty: True if the label represents an empty label, False otherwise
    :var parent_id: Optional name of the parent label, if any
    :var revisit_affected_annotations: Optional, whether to mark the existing
        annotations containing that label as 'to revisit'
    :var is_deleted: whether a label is deleted or not
    """

    name: str
    task_title: str
    domain: Domain
    group: str | None = None
    is_empty: bool = False
    hotkey: str = ""
    color: str = ""
    id: str | None = None
    parent_id: str | None = None
    revisit_affected_annotations: bool | None = None
    is_deleted: bool = False

    @classmethod
    def from_rest_and_task_details(
        cls, data_dict: dict[str, Any], task_title: str, task_type: TaskType
    ) -> "LabelProperties":
        """
        Instantiates a LabelProperties object from a dictionary `data_dict`.
        `data_dict` should contain the REST representation of a Label

        :param data_dict: Dictionary holding the REST representation of the label
        :param task_title: Title of the task to which the label belongs
        :param task_type: Type of the task to which the label belongs
        """
        property_dict: dict[str, Any] = {}
        # We only consider those label properties that are defined in this dataclass,
        # other properties are discarded
        for key, value in data_dict.items():
            if key in [field.name for field in fields(cls)]:
                property_dict[key] = value
        return cls(
            **property_dict,
            task_title=task_title,
            domain=task_type.domain,
        )


class ProjectRestValidator(RestApiValidator):
    def __init__(self) -> None:
        base_dir = os.path.dirname(__file__) + "/../../../api/schemas/"
        self.create_project_schema = self.load_schema_file_as_dict(base_dir + "projects/requests/post/project.yaml")
        self.update_project_schema = self.load_schema_file_as_dict(base_dir + "projects/requests/put/project.yaml")

    @staticmethod
    def _get_labels_from_rest(data: dict[str, Any], include_deleted: bool = False) -> list[LabelProperties]:
        """
        Returns a list of the properties of the Labels for all tasks in the
        request data

        :param data: REST request data representing a project
        :param include_deleted: Boolean that includes deleted labels when true
        :return: List of LabelProperties, each entry representing the properties
            for a single label that are up for validation
        """
        labels: list[LabelProperties] = []
        for task in data[PIPELINE][TASKS]:
            task_type_str = task[TASK_TYPE].upper()
            task_type = TaskType[task_type_str]
            for label in task.get(LABELS, []):
                label_properties = LabelProperties.from_rest_and_task_details(
                    data_dict=label,
                    task_title=task[TITLE],
                    task_type=task_type,
                )

                if not label_properties.is_deleted or include_deleted:
                    labels.append(label_properties)

        return labels


class RestProjectParser(ProjectParser):
    """
    Parser that can read and decode the information necessary to create
    a project from the JSON-like dictionary of the project creation endpoint.

    :param rest_data: JSON-like dict input data as from the project creation endpoint
    """

    base_dir = os.path.dirname(__file__) + "/../../../api/schemas/"
    json_schema = ProjectRestValidator().load_schema_file_as_dict(base_dir + "projects/requests/post/project.yaml")

    def __init__(self, rest_data: dict[str, Any]) -> None:
        self.__rest_data = rest_data
        # JSON-schema validation
        jsonschema.validate(rest_data, self.json_schema)

    def get_project_name(self) -> str:
        return self.__rest_data[NAME]

    def _get_connections_rest(self) -> list[dict]:
        return self.__rest_data[PIPELINE][CONNECTIONS]

    def get_connections(self) -> tuple[tuple[str, str], ...]:
        connections_rest = self._get_connections_rest()
        return tuple((conn_rest[FROM], conn_rest[TO]) for conn_rest in connections_rest)

    def _get_tasks_rest(self) -> list[dict]:
        return self.__rest_data[PIPELINE][TASKS]

    def get_tasks_names(self) -> tuple[str, ...]:
        return tuple(task_rest[TITLE] for task_rest in self._get_tasks_rest())

    @lru_cache(maxsize=4)
    def _get_task_rest(self, task_name: str) -> dict[str, Any]:
        try:
            return next(task_rest for task_rest in self._get_tasks_rest() if task_rest[TITLE] == task_name)
        except StopIteration as ex:
            if task_name not in self.get_tasks_names():
                raise ValueError(f"Task with name '{task_name}' not found") from ex
            raise ProjectParserInternalError(f"Error while fetching data for task with name '{task_name}'") from ex

    def get_task_type_by_name(self, task_name: str) -> TaskType:
        task_rest = self._get_task_rest(task_name=task_name)
        task_type = task_rest[TASK_TYPE].upper()
        if task_type == "ANOMALY":
            return TaskType.ANOMALY_CLASSIFICATION
        return TaskType[task_type]

    def get_custom_labels_names_by_task(self, task_name: str) -> tuple[str, ...]:
        task_rest = self._get_task_rest(task_name=task_name)
        return tuple(
            label_rest[NAME] for label_rest in task_rest.get("labels", []) if not label_rest.get(IS_EMPTY, False)
        )

    @lru_cache(maxsize=32)
    def _get_label_rest(self, task_name: str, label_name: str) -> dict[str, Any]:
        try:
            return next(
                label_rest
                for label_rest in self._get_task_rest(task_name=task_name)[LABELS]
                if label_rest[NAME] == label_name
            )
        except StopIteration as ex:
            if label_name not in self.get_custom_labels_names_by_task(task_name=task_name):
                raise ValueError(f"Label with name '{label_name}' not found in task '{task_name}'") from ex
            raise ProjectParserInternalError(
                f"Error while fetching data for label with name '{label_name}' in task '{task_name}'"
            ) from ex

    def get_label_group_by_name(self, task_name: str, label_name: str) -> str:
        label_rest = self._get_label_rest(task_name=task_name, label_name=label_name)
        return label_rest[GROUP]

    def get_label_hotkey_by_name(self, task_name: str, label_name: str) -> str:
        label_rest = self._get_label_rest(task_name=task_name, label_name=label_name)
        hotkey = label_rest.get(HOTKEY, "")
        return hotkey if hotkey else ""

    def get_label_color_by_name(self, task_name: str, label_name: str) -> str:
        label_rest = self._get_label_rest(task_name=task_name, label_name=label_name)
        color = label_rest.get(COLOR, "")
        return color if color else ""

    def get_label_parent_by_name(self, task_name: str, label_name: str) -> str:
        label_rest = self._get_label_rest(task_name=task_name, label_name=label_name)
        parent = label_rest.get(PARENT_ID, "")
        return parent if parent else ""

    def get_keypoint_structure_data(self, task_name: str) -> dict[str, list]:
        task_data = self._get_task_rest(task_name=task_name)
        return task_data.get("keypoint_structure", {})


class RestProjectUpdateParser(RestProjectParser, ProjectUpdateParser):
    """
    Parser that can read and decode the information necessary to update an existing
    project from the JSON-like dictionary of the project update endpoint.

    :param rest_data: JSON-like dict input data as from the project update endpoint
    """

    base_dir = os.path.dirname(__file__) + "/../../../api/schemas/"
    json_schema = ProjectRestValidator().load_schema_file_as_dict(base_dir + "projects/requests/put/project.yaml")

    def __init__(self, rest_data: dict[str, Any]) -> None:
        super().__init__(rest_data=rest_data)

    def get_connections(self) -> tuple[tuple[ID, ID], ...]:
        connections_rest = self._get_connections_rest()
        return tuple((ID(conn_rest[FROM]), ID(conn_rest[TO])) for conn_rest in connections_rest)

    @lru_cache(maxsize=4)
    def get_task_id_by_name(self, task_name: str) -> ID:
        task_rest = self._get_task_rest(task_name=task_name)
        return task_rest[ID_]

    @lru_cache(maxsize=32)
    def get_label_id_by_name(self, task_name: str, label_name: str) -> ID | None:
        label_rest = self._get_label_rest(task_name=task_name, label_name=label_name)
        return label_rest.get(ID_)

    def get_added_labels_names_by_task(self, task_name: str) -> tuple[str, ...]:
        # Added labels can be identified by their lack of id field
        label_names = self.get_custom_labels_names_by_task(task_name=task_name)
        return tuple(
            label_name
            for label_name in label_names
            if self.get_label_id_by_name(task_name=task_name, label_name=label_name) is None
        )

    def get_deleted_labels_names_by_task(self, task_name: str) -> tuple[str, ...]:
        # Deleted labels have a field 'is_deleted=true'
        label_names = self.get_custom_labels_names_by_task(task_name=task_name)
        return tuple(
            label_name
            for label_name in label_names
            if self._get_label_rest(task_name=task_name, label_name=label_name).get(IS_DELETED, False)
        )

    def get_revisit_state_by_label_name(self, task_name: str, label_name: str) -> bool:
        label_rest = self._get_label_rest(task_name=task_name, label_name=label_name)
        return label_rest.get(REVISIT_AFFECTED_ANNOTATIONS, False)


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
            self._label_schema = LabelSchemaRepo(self.project.identifier).get_latest()
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
            self._label_schema_1 = LabelSchemaRepo(self.project.identifier).get_latest_view_by_task(
                task_node_id=self.task_node_1.id_
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
            self._label_schema_2 = LabelSchemaRepo(self.project.identifier).get_latest_view_by_task(
                task_node_id=self.task_node_2.id_
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
        self,
        detection_labels: list[Label],
        classification_labels: list[Label] | None = None,
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

    def _set_auto_train(self, auto_train: bool = False):
        for task_node in self.project.get_trainable_task_nodes():
            task_config = TaskNodeConfig()
            task_config.auto_training = auto_train
            conf_params: ComponentParameters[TaskNodeConfig] = ComponentParameters(
                workspace_id=self.workspace_id,
                project_id=self.project.id_,
                component=ComponentType.TASK_NODE,
                id_=ConfigurableParametersRepo.generate_id(),
                data=task_config,
                task_id=task_node.id_,
            )
            ConfigurableParametersRepo(self.project_identifier).save(conf_params)

    def cleanup(self) -> None:
        DeletionHelpers.delete_project_by_id(project_id=self.project.id_)


@pytest.fixture
def fxt_db_project_service() -> Generator[DBProjectService, None, None]:
    db_project_service = DBProjectService()

    yield db_project_service

    db_project_service.cleanup()
