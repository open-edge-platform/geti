# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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

"""
Defines train workflow data and getter utils
"""

import typing
from dataclasses import dataclass

from dataclasses_json import dataclass_json
from geti_types import ID, DatasetStorageIdentifier, ProjectIdentifier
from jobs_common_extras.mlflow.utils.train_output_models import TrainOutputModelIds
from sc_sdk.configuration.elements.hyper_parameters import HyperParameters
from sc_sdk.entities.compiled_dataset_shards import CompiledDatasetShards, NullCompiledDatasetShards
from sc_sdk.entities.datasets import Dataset
from sc_sdk.entities.label_schema import LabelSchema, LabelSchemaView
from sc_sdk.entities.model import Model
from sc_sdk.entities.model_storage import ModelStorage, ModelStorageIdentifier
from sc_sdk.entities.project import Project
from sc_sdk.entities.task_node import TaskNode
from sc_sdk.repos import LabelSchemaRepo, ModelRepo, ModelStorageRepo, ProjectRepo, TaskNodeRepo
from sc_sdk.repos.compiled_dataset_shards_repo import CompiledDatasetShardsRepo
from sc_sdk.repos.configurable_parameters_repo import ConfigurableParametersRepo
from sc_sdk.repos.dataset_repo import DatasetRepo


@dataclass_json
@dataclass
class TrainWorkflowData:
    """
    Data class defining data used for training and providing helpers to get
    frequently used objects

    :param workspace_id: Workspace ID
    :param project_id: Project ID
    :param task_id: Task ID
    :param from_scratch: Whether to train the task from scratch.
    :param should_activate_model: Whether to activate model after training
    :param infer_on_pipeline: Whether to infer on pipeline
    :param model_storage_id: ID of model storage of the model to train
    :param compiled_dataset_shards_id: Optional, model will be trained on the dataset shard files if not None
    :param min_annotation_size: Minimum size of an annotation in pixels. Any annotation smaller than this will be
        ignored during training
    :param max_number_of_annotations: Maximum number of annotation allowed in one annotation scene. If exceeded, the
    annotation scene will be ignored during training.
    :param reshuffle_subsets: Whether to reassign/shuffle all the items to subsets including Test set from scratch
    """

    workspace_id: str
    project_id: str
    task_id: str
    label_schema_id: str
    model_storage_id: str
    hyperparameters_id: str
    from_scratch: bool
    should_activate_model: bool
    infer_on_pipeline: bool
    active_model_id: str
    input_model_id: typing.Optional[str]  # noqa: UP007
    compiled_dataset_shards_id: typing.Optional[str]  # noqa: UP007
    min_annotation_size: typing.Optional[int] = None  # noqa: UP007
    max_number_of_annotations: typing.Optional[int] = None  # noqa: UP007
    reshuffle_subsets: bool = False

    def get_common_entities(self) -> tuple[Project, TaskNode]:
        """
        Get workspace, project, and task node associated with a train workflow
        :return: Tuple[Workspace, Project, TaskNode]
        """
        project = ProjectRepo().get_by_id(ID(self.project_id))
        task_node = TaskNodeRepo(project.identifier).get_by_id(ID(self.task_id))
        return project, task_node

    def get_label_schema(self) -> LabelSchema | LabelSchemaView:
        """
        Get label schema associated with a train workflow
        :return: Union[LabelSchema, LabelSchemaView]
        """
        project_identifier = ProjectIdentifier(workspace_id=ID(self.workspace_id), project_id=ID(self.project_id))
        return LabelSchemaRepo(project_identifier).get_by_id(ID(self.label_schema_id))

    def get_model_storage_identifier(self) -> ModelStorageIdentifier:
        """
        Get the identifier of the model storage associated with the train workflow
        :return: ModelStorageIdentifier
        """
        return ModelStorageIdentifier(
            workspace_id=ID(self.workspace_id),
            project_id=ID(self.project_id),
            model_storage_id=ID(self.model_storage_id),
        )

    def get_model_storage(self) -> ModelStorage:
        """
        Get the model storage associated with a train workflow
        :return: ModelStorage
        """
        project_identifier = ProjectIdentifier(workspace_id=ID(self.workspace_id), project_id=ID(self.project_id))
        return ModelStorageRepo(project_identifier).get_by_id(ID(self.model_storage_id))

    def get_input_model(self) -> Model | None:
        """
        Get the input model associated with a train workflow if one exists, else return None
        :return: Optional[Model]
        """
        project_identifier = ProjectIdentifier(workspace_id=ID(self.workspace_id), project_id=ID(self.project_id))
        model_storage = ModelStorageRepo(project_identifier).get_by_id(ID(self.model_storage_id))
        if self.input_model_id is None:
            return None
        return ModelRepo(model_storage.identifier).get_by_id(ID(self.input_model_id))

    def get_dataset(self, dataset_id: str) -> Dataset:
        """
        Get the dataset from the given dataset_id
        :return: Dataset
        """
        project, _ = self.get_common_entities()
        dataset_storage = project.get_training_dataset_storage()
        dataset_repo = DatasetRepo(dataset_storage.identifier)
        return dataset_repo.get_by_id(ID(dataset_id))

    def get_compiled_dataset_shards(
        self,
    ) -> CompiledDatasetShards | NullCompiledDatasetShards:
        """Get the CompiledDatasetShards entity.

        :return CompiledDatasetShards | None: If the given id is None, return `NullCompiledDatasetShards`.
            Otherwise, return the entity from DB.
        """
        if self.compiled_dataset_shards_id is None:
            return NullCompiledDatasetShards()

        project = ProjectRepo().get_by_id(ID(self.project_id))
        dataset_storage_id = project.get_training_dataset_storage().id_

        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=ID(self.workspace_id),
            project_id=ID(self.project_id),
            dataset_storage_id=dataset_storage_id,
        )

        repo = CompiledDatasetShardsRepo(dataset_storage_identifier=dataset_storage_identifier)
        return repo.get_by_id(id_=ID(self.compiled_dataset_shards_id))

    def get_hyper_parameters(self) -> HyperParameters:
        """Get the HyperParameters entity.

        :return HyperParameters: Return HyperParameters entity from given hyperparameters_id and project_id
        """
        project = ProjectRepo().get_by_id(ID(self.project_id))
        config_params_repo = ConfigurableParametersRepo(project.identifier)
        return typing.cast("HyperParameters", config_params_repo.get_by_id(ID(self.hyperparameters_id)))


@dataclass_json
@dataclass
class TrainWorkflowDataForFlyteTaskTrainer:
    """Dataclass to store everything required for Flyte task based model training."""

    train_data: TrainWorkflowData
    dataset_id: str
    organization_id: str
    job_id: str
    train_output_model_ids: TrainOutputModelIds

    @property
    def project_identifier(self) -> ProjectIdentifier:
        return ProjectIdentifier(
            workspace_id=ID(self.train_data.workspace_id),
            project_id=ID(self.train_data.project_id),
        )
