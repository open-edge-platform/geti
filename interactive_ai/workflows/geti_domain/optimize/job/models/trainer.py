# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""Define dataclass for data passing between optimization tasks."""

from dataclasses import dataclass

from dataclasses_json import dataclass_json
from geti_types import ID, ProjectIdentifier
from iai_core_py.entities.model import Model
from iai_core_py.entities.model_storage import ModelStorageIdentifier
from iai_core_py.repos import ModelRepo
from jobs_common.k8s_helpers.k8s_resources_calculation import ComputeResources, EphemeralStorageResources
from jobs_common.k8s_helpers.trainer_image_info import TrainerImageInfo
from jobs_common.tasks.utils.secrets import JobMetadata

from .config import OptimizationConfig


@dataclass_json
@dataclass
class OptimizationTrainerContext:
    """Dataclass to collect entities after model optimize preparation step.
    Unlike `OptimizationConfig`, this object is JSON serializable, so that it can be
    used for communication between Flyte tasks.
    """

    workspace_id: str
    project_id: str
    job_id: str
    input_model_id: str
    model_to_optimize_id: str
    model_storage_id: str
    ephemeral_storage_resources: EphemeralStorageResources
    compute_resources: ComputeResources
    trainer_image_info: TrainerImageInfo

    @classmethod
    def create_from_config(cls, optimization_cfg: OptimizationConfig) -> "OptimizationTrainerContext":
        ephemeral_storage_resources = EphemeralStorageResources.create_from_compiled_dataset_shards(
            compiled_dataset_shards=optimization_cfg.compiled_dataset_shards,
            ephemeral_storage_safety_margin=5 * (1024**3),  # 5Gi
        )
        job_metadata = JobMetadata.from_env_vars()

        return cls(
            workspace_id=str(optimization_cfg.project.workspace_id),
            project_id=str(optimization_cfg.project.id_),
            job_id=str(job_metadata.id),
            input_model_id=str(optimization_cfg.input_model.id_),
            model_to_optimize_id=str(optimization_cfg.model_to_optimize.id_),
            model_storage_id=str(optimization_cfg.model_storage_identifier.model_storage_id),
            ephemeral_storage_resources=ephemeral_storage_resources,
            compute_resources=ComputeResources.from_node_resources(),
            trainer_image_info=TrainerImageInfo.create(
                training_framework=optimization_cfg.input_model.training_framework
            ),
        )

    @property
    def project_identifier(self) -> ProjectIdentifier:
        return ProjectIdentifier(workspace_id=ID(self.workspace_id), project_id=ID(self.project_id))

    @property
    def model_storage_identifier(self) -> ModelStorageIdentifier:
        return ModelStorageIdentifier(
            workspace_id=ID(self.workspace_id),
            project_id=ID(self.project_id),
            model_storage_id=ID(self.model_storage_id),
        )

    @property
    def input_model(self) -> Model:
        return ModelRepo(
            model_storage_identifier=self.model_storage_identifier,
        ).get_by_id(id_=ID(self.input_model_id))

    @property
    def model_to_optimize(self) -> Model:
        return ModelRepo(
            model_storage_identifier=self.model_storage_identifier,
        ).get_by_id(id_=ID(self.model_to_optimize_id))
