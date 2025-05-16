# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module contains the TrainOutputModels class that is used for bookkeeping the
output models of a training
"""

import typing
from dataclasses import dataclass
from typing import overload

from dataclasses_json import dataclass_json
from geti_telemetry_tools import unified_tracing
from geti_types import ID
from iai_core.entities.model import Model, ModelStatus, ModelStorageIdentifier
from iai_core.repos import ModelRepo
from iai_core.services import ModelService
from iai_core.utils.time_utils import now

from jobs_common.tasks.utils.secrets import JobMetadata
from jobs_common_extras.mlflow.adapters.geti_otx_interface import GetiOTXInterfaceAdapter


@dataclass_json
@dataclass
class TrainOutputModelIds:
    """Class used to store different training output models' id only."""

    base: str
    mo_with_xai: str
    mo_fp32_without_xai: typing.Optional[str]  # noqa: UP007
    mo_fp16_without_xai: typing.Optional[str]  # noqa: UP007
    onnx: typing.Optional[str]  # noqa: UP007


@dataclass
class TrainOutputModels:
    """
    Class used to store different output models from training
    """

    base: Model  # The trained model in the base framework format
    mo_with_xai: Model  # The OpenVino model with eXplainable AI (saliency maps)
    mo_fp32_without_xai: typing.Optional[Model] = None  # noqa: UP007 # The OpenVino model without eXplainable AI
    mo_fp16_without_xai: typing.Optional[Model] = None  # noqa: UP007 # The OpenVino model with lower precision FP16
    onnx: typing.Optional[Model] = None  # noqa: UP007  # The ONNX model

    def get_all_models(self) -> list[Model]:
        """
        Return all output models
        """
        return [model for model in vars(self).values() if isinstance(model, Model)]

    def reload_models(self, from_bucket: bool) -> None:
        """
        Reload all the models from the DB

        :param from_bucket: If true, reload the model from the S3 bucket.
            Otherwise, reload it from DB.
        """
        if from_bucket:
            self._reload_from_bucket()
        else:
            self._reload_from_db()

    @unified_tracing
    def _reload_from_bucket(self) -> None:
        project_identifier = self.base.get_project().identifier
        adapter = GetiOTXInterfaceAdapter(
            project_identifier=project_identifier,
            job_metadata=JobMetadata.from_env_vars(),
        )
        models_to_update = self.get_all_models()
        adapter.update_output_models(models_to_update=models_to_update)

        performance = adapter.pull_metrics()
        if performance is not None:
            self.base.performance = performance

        # Should save to DB to apply the updated fields
        for model in models_to_update:
            ModelService.save_with_auto_archival(model=model, identifier=self.base.model_storage_identifier)

    @unified_tracing
    def _reload_from_db(self) -> None:
        model_repo = ModelRepo(self.base.model_storage_identifier)
        for attr_name, model in vars(self).items():
            if model is not None:
                setattr(self, attr_name, model_repo.get_by_id(model.id_))

    @unified_tracing
    def set_models_training_duration(self) -> None:
        """
        Set a given training duration to all the models in the command (base and optimized).
        This method updates the corresponding attribute in the database.
        """
        model_repo = ModelRepo(self.base.model_storage_identifier)
        training_duration = (now() - self.base.creation_date).total_seconds()

        for model in self.get_all_models():
            model_repo.update_training_duration(model=model, training_duration=training_duration)

    def set_models_status(self, model_status: ModelStatus) -> None:
        """
        Set a given model status to all the models in the command (base and optimized).
        This method updates the corresponding attribute in the database.

        :param model_status: ModelStatus to set for each model
        """
        model_repo = ModelRepo(self.base.model_storage_identifier)

        for model in self.get_all_models():
            model_repo.update_model_status(model=model, model_status=model_status)

    def to_train_output_model_ids(self) -> TrainOutputModelIds:
        def _parse(model: Model | None) -> str | None:
            return str(model.id_) if model is not None else None

        return TrainOutputModelIds(
            base=str(self.base.id_),
            mo_with_xai=str(self.mo_with_xai.id_),
            mo_fp32_without_xai=_parse(self.mo_fp32_without_xai),
            mo_fp16_without_xai=_parse(self.mo_fp16_without_xai),
            onnx=_parse(self.onnx),
        )

    @classmethod
    def from_train_output_model_ids(
        cls,
        train_output_model_ids: TrainOutputModelIds,
        model_storage_identifier: ModelStorageIdentifier,
    ) -> "TrainOutputModels":
        model_repo = ModelRepo(model_storage_identifier)

        @overload
        def _parse(id_: str) -> Model: ...

        @overload
        def _parse(id_: None) -> None: ...

        def _parse(id_: str | None) -> Model | None:
            if id_ is None:
                return None
            return model_repo.get_by_id(id_=ID(id_))

        return cls(
            base=_parse(train_output_model_ids.base),
            mo_with_xai=_parse(train_output_model_ids.mo_with_xai),
            mo_fp32_without_xai=_parse(train_output_model_ids.mo_fp32_without_xai),
            mo_fp16_without_xai=_parse(train_output_model_ids.mo_fp16_without_xai),
            onnx=_parse(train_output_model_ids.onnx),
        )
