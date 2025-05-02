# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the repository for model entities
"""

import logging
from collections.abc import Callable, Sequence
from enum import Enum
from typing import Any

from pymongo import DESCENDING, IndexModel
from pymongo.client_session import ClientSession
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from iai_core_py.adapters.model_adapter import DataSource
from iai_core_py.entities.model import Model, ModelFormat, ModelOptimizationType, ModelPrecision, ModelStatus, NullModel
from iai_core_py.entities.model_storage import ModelStorageIdentifier
from iai_core_py.repos.base.model_storage_based_repo import ModelStorageBasedSessionRepo
from iai_core_py.repos.base.session_repo import QueryAccessMode
from iai_core_py.repos.mappers.cursor_iterator import CursorIterator
from iai_core_py.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from iai_core_py.repos.mappers.mongodb_mappers.model_mapper import ModelPurgeInfoToMongo, ModelToMongo
from iai_core_py.repos.storage.binary_repos import ModelBinaryRepo

from geti_types import ID, Session

logger = logging.getLogger(__name__)


class ModelStatusFilter(Enum):
    """enum used to filter models by a list of status' in the model repo"""

    # Models that underwent a successful training cycle and improved.
    IMPROVED = [ModelStatus.SUCCESS.name]

    # Models that underwent a successful training cycle regardless of improvement.
    TRAINED = [
        ModelStatus.NOT_IMPROVED.name,
        ModelStatus.SUCCESS.name,
        ModelStatus.TRAINED_NO_STATS.name,
    ]

    # All models except ones that failed
    NON_FAILED = [status.name for status in ModelStatus if status is not ModelStatus.FAILED]

    # All models
    ALL = [status.name for status in ModelStatus]


class ModelRepo(ModelStorageBasedSessionRepo[Model]):
    """
    Repository to persist Model entities in the database.

    :param model_storage_identifier: Identifier of the model storage
    :param session: Session object; if not provided, it is loaded through get_session()
    """

    collection_name = "model"

    def __init__(self, model_storage_identifier: ModelStorageIdentifier, session: Session | None = None) -> None:
        super().__init__(
            collection_name=ModelRepo.collection_name,
            model_storage_identifier=model_storage_identifier,
            session=session,
        )
        # binary repos are initialized lazily when needed
        self.__binary_repo: ModelBinaryRepo | None = None

    @property
    def forward_map(self) -> Callable[[Model], dict]:
        return ModelToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], Model]:
        return ModelToMongo.backward

    @property
    def null_object(self) -> NullModel:
        return NullModel()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor,
            mapper=ModelToMongo,
            parameter=None,
        )

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [
            IndexModel([("previous_trained_revision_id", DESCENDING)]),
            IndexModel([("model_storage_id", DESCENDING), ("version", DESCENDING)]),
            # Below index needed to report total GPU training time metric
            IndexModel([("model_format", DESCENDING), ("training_duration", DESCENDING)]),
        ]
        return super_indexes + new_indexes

    @property
    def binary_repo(self) -> ModelBinaryRepo:
        """Binary repo relative to the model repo"""
        if self.__binary_repo is None:
            self.__binary_repo = ModelBinaryRepo(self.identifier)
        return self.__binary_repo

    def _offload_binary_data(self, model: Model) -> None:
        """
        Store the model binary data to the database and replace the in-memory
        data with an adapter (DataSource) that can be used to fetch it lazily.

        :param model: Model containing the binary data to offload
        """
        for name, adapter in list(model.model_adapters.items()):
            if not adapter.from_file_storage:
                # There is not a file on storage for the adapter. Make it, and save it
                binary_filename = self.binary_repo.save(dst_file_name=name, data_source=adapter.data, make_unique=True)
                data_source = DataSource(repository=self.binary_repo, binary_filename=binary_filename)
                model.set_data(name, data_source, skip_deletion=True)
        if model.exportable_code_adapter is not None and not model.exportable_code_adapter.from_file_storage:
            binary_filename = self.binary_repo.save(
                dst_file_name="exportable_code.whl", data_source=model.exportable_code_adapter.data, make_unique=True
            )
            data_source = DataSource(repository=self.binary_repo, binary_filename=binary_filename)
            model.exportable_code = data_source  # type: ignore

    def save(self, instance: Model, mongodb_session: ClientSession | None = None) -> None:
        """
        Save a model to the database and its binary data to the persisted storage.

        If a document with the same id already exists, it is overwritten.
        Otherwise, a new document is created.

        :param instance: Model to save
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        """
        self._offload_binary_data(instance)
        super().save(instance, mongodb_session=mongodb_session)

    def save_many(self, instances: Sequence[Model], mongodb_session: ClientSession | None = None) -> None:
        """
        Save multiple models of the same type to the database

        Any existing document with the same id of one of the provided instances will be
        overwritten; a new document is created otherwise.

        :param instances: Sequence of Model objects to save
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        """
        for instance in instances:
            self.save(instance, mongodb_session=mongodb_session)

    def get_all_by_status_and_type(
        self,
        *,
        model_status_filter: ModelStatusFilter = ModelStatusFilter.ALL,
        include_optimized_models: bool = True,
        latest_first: bool = True,
    ) -> CursorIterator[Model]:
        """
        Get all the models filtered by status.

        :param model_status_filter: Filter to apply to the models. See 'ModelStatusFilter'
        :param include_optimized_models: Whether to include the optimized models
            in the output or not.
        :param latest_first: Whether to sort the output entities by creation date
            in ascending or descending order
        :return: Model CursorIterator
        """
        sort_info = [("_id", -1 if latest_first else 1)]
        status_type_filter: dict[str, Any] = {}

        if model_status_filter != ModelStatusFilter.ALL:
            status_type_filter["model_status"] = {"$in": model_status_filter.value}

        if not include_optimized_models:
            status_type_filter["optimization_type"] = ModelOptimizationType.NONE.name

        return self.get_all(extra_filter=status_type_filter, sort_info=sort_info)

    def get_latest_successful_version(self) -> int:
        """
        Get the latest (highest) version of any model in the collection

        :return: version of the latest successful model in the storage; 0 if not found
        """
        pipeline: list[dict] = [
            {"$match": {"model_status": ModelStatus.SUCCESS.name}},
            {"$sort": {"version": -1}},
            {"$limit": 1},
            {"$project": {"version": 1}},
        ]
        docs = list(self.aggregate_read(pipeline))
        if len(docs) == 0:
            return 0
        return docs[0].get("version", 0)

    def get_optimized_models_by_trained_revision_id(
        self,
        trained_revision_id: ID,
        model_status_filter: ModelStatusFilter = ModelStatusFilter.NON_FAILED,
        leaf_only: bool = False,
    ) -> list[Model]:
        """
        Find all the optimized models that are build from the passed trained_revision_id

        :param trained_revision_id: ID of base model the optimized models refer to
        :param model_status_filter: Filter to apply to the models. See 'ModelStatusFilter'
        :param leaf_only: Whether to include only models that represent the final
            artifact for an optimization pipeline, i.e. NOT intermediate models that
            are used as inputs to other optimization/conversion steps.
        :return: List of optimized models
        """
        optimized_models = []
        revision_and_status_filter: dict[str, Any] = {}
        if trained_revision_id != ID():
            if model_status_filter != ModelStatusFilter.ALL:
                revision_and_status_filter["model_status"] = {"$in": model_status_filter.value}
            revision_and_status_filter["previous_trained_revision_id"] = IDToMongo.forward(trained_revision_id)
            models = self.get_all(extra_filter=revision_and_status_filter, sort_info=[("_id", -1)])
            optimized_models = [model for model in models if model.is_optimized()]
            if leaf_only:
                # Find the models pointed by other ones (intermediate) and exclude them
                intermediate_ids = {m.previous_revision_id for m in optimized_models}  # type: ignore[union-attr]
                optimized_models = [m for m in optimized_models if m.id_ not in intermediate_ids]
        return optimized_models

    def get_optimized_models_by_base_model_id(self, base_model_id: ID) -> CursorIterator[Model]:
        """
        Get models optimized models derived from base model with given id

        :param base_model_id: the id of base model
        """
        revision_and_optimization_filter = {
            "optimization_type": {"$ne": ModelOptimizationType.NONE.name},
            "previous_trained_revision_id": IDToMongo.forward(base_model_id),
        }
        return self.get_all(extra_filter=revision_and_optimization_filter)

    def get_all_equivalent_model_ids(self, model: Model) -> tuple[ID, ...]:
        """
        Returns all the equivalent models related to the given model.
        The models are considered equivalent if and only if they are indistinguishable
        from the predictions PoV, that is if they originate from the same base framework
        model and underwent the same post-training performance-changing optimizations.

        :param model: The model for which to find its equivalent models
        :return: A tuple with the equivalent model IDs
        """
        equivalent_predict_optimization_types = [
            ModelOptimizationType.NONE,
            ModelOptimizationType.MO,
            ModelOptimizationType.ONNX,
        ]
        if model.optimization_type in equivalent_predict_optimization_types:
            trained_revision_id = (
                model.id_ if model.model_format == ModelFormat.BASE_FRAMEWORK else model.previous_trained_revision_id
            )
            query = {
                "optimization_type": {"$in": [opt.name for opt in equivalent_predict_optimization_types]},
                "$or": [
                    {"previous_trained_revision_id": IDToMongo.forward(trained_revision_id)},
                    {"_id": IDToMongo.forward(trained_revision_id)},
                ],
                "version": model.version,
            }
        else:  # for optimized model check that optimization flow is identical too
            optimization_methods = [om.name for om in model.optimization_methods] if model.optimization_methods else []
            query = {
                "previous_trained_revision_id": IDToMongo.forward(model.previous_trained_revision_id),
                "optimization_type": model.optimization_type.name,
                "optimization_methods": optimization_methods,
                "optimization_objectives": model.optimization_objectives,
                "precision": [p.name for p in model.precision],
                "target_device": model.target_device.name,
            }
        return tuple(self.get_all_ids(extra_filter=query))

    def has_models(
        self,
        *,
        model_status_filter: ModelStatusFilter = ModelStatusFilter.ALL,
    ) -> bool:
        """
        Check whether a storage has any models.

        :param model_status_filter: Filter to apply to the models. See 'ModelStatusFilter'
        :return: ``True`` if a matching model was found, ``False`` otherwise.
        """
        query: dict[str, Any] = {}
        if model_status_filter != ModelStatusFilter.ALL:
            query["model_status"] = {"$in": model_status_filter.value}
        count = self.count(extra_filter=query)
        return count > 0

    def __get_latest_model_by_status_aggr_pipeline(
        self,
        *,
        model_status_filter: ModelStatusFilter,
        tags: list[str] | None = None,
        newer_than_id: ID | None = None,
        include_optimized_models: bool = False,
    ) -> list[dict]:
        match_condition: dict[str, Any] = {}
        if model_status_filter != ModelStatusFilter.ALL:
            match_condition["model_status"] = {"$in": model_status_filter.value}

        if tags is not None and len(tags) > 0:
            match_condition.update({"tags": {"$all": tags}})

        if not include_optimized_models:
            match_condition["optimization_type"] = ModelOptimizationType.NONE.name

        if newer_than_id is not None and newer_than_id != ID():
            match_condition["_id"] = {"$gte": IDToMongo.forward(newer_than_id)}

        return [{"$match": match_condition}, {"$sort": {"version": -1, "_id": -1}}, {"$limit": 1}]

    def _get_latest_model_by_status(
        self,
        *,
        tags: list[str] | None = None,
        model_status_filter: ModelStatusFilter = ModelStatusFilter.ALL,
        newer_than_id: ID | None = None,
        include_optimized_models: bool = False,
    ) -> Model:
        aggr_pipeline = self.__get_latest_model_by_status_aggr_pipeline(
            model_status_filter=model_status_filter,
            tags=tags,
            newer_than_id=newer_than_id,
            include_optimized_models=include_optimized_models,
        )
        matched_docs = list(self.aggregate_read(aggr_pipeline))
        if not matched_docs:
            return NullModel()
        return ModelToMongo.backward(matched_docs[0])

    def _get_latest_model_id_by_status(
        self,
        *,
        tags: list[str] | None = None,
        model_status_filter: ModelStatusFilter = ModelStatusFilter.ALL,
        newer_than_id: ID | None = None,
        include_optimized_models: bool = False,
    ) -> ID:
        aggr_pipeline = self.__get_latest_model_by_status_aggr_pipeline(
            model_status_filter=model_status_filter,
            tags=tags,
            newer_than_id=newer_than_id,
            include_optimized_models=include_optimized_models,
        )
        aggr_pipeline.append({"$project": {"_id": 1}})
        matched_docs = list(self.aggregate_read(aggr_pipeline))
        if not matched_docs:
            return ID()
        return IDToMongo.backward(matched_docs[0]["_id"])

    def get_latest(
        self,
        *,
        tags: list[str] | None = None,
        model_status_filter: ModelStatusFilter = ModelStatusFilter.ALL,
        newer_than_id: ID | None = None,
        include_optimized_models: bool = False,
    ) -> Model:
        """
        Get the most recent model from the database.

        :param tags: Optional list of tags which the model must contain
            to further filter the search
        :param model_status_filter: Filter to apply to the models. See 'ModelStatusFilter'
        :param newer_than_id: Optional. Filter out annotations older than this ID
        :param include_optimized_models: filter including or excluding optimized models
        :return: Latest model entity if any or :class:`~iai_core_py.entities.model.NullModel`
            if not found
        """
        return self._get_latest_model_by_status(
            tags=tags,
            model_status_filter=model_status_filter,
            newer_than_id=newer_than_id,
            include_optimized_models=include_optimized_models,
        )

    def __get_latest_model_for_inference_query(
        self, base_model_id: ID, model_status_filter: ModelStatusFilter
    ) -> dict[str, Any]:
        # Query to search the MO model used for inference given the base model ID
        return {
            "previous_trained_revision_id": IDToMongo.forward(base_model_id),
            "optimization_type": ModelOptimizationType.MO.name,
            "has_xai_head": True,
            "precision": [ModelPrecision.FP32.name],
            "model_status": {"$in": model_status_filter.value},
        }

    def get_latest_model_for_inference(
        self,
        base_model_id: ID | None = None,
        model_status_filter: ModelStatusFilter = ModelStatusFilter.IMPROVED,
    ) -> Model:
        """
        Get the MO FP32 with XAI head version of the latest base framework model.
        This model is used for inference.

        :base_model_id: Optional ID for which to get the latest inference model
        :model_status_filter: Optional ModelStatusFilter to apply in query
        :return: The MO model or :class:`~iai_core_py.entities.model.NullModel` if not found
        """
        # Get the ID of the latest base framework model
        if base_model_id is None:
            base_model_id = self._get_latest_model_id_by_status(model_status_filter=model_status_filter)
        if base_model_id == ID():
            return NullModel()

        # Use the base model ID to search for the MO model
        query = self.__get_latest_model_for_inference_query(
            base_model_id=base_model_id, model_status_filter=model_status_filter
        )

        # Use ascending order sorting to retrieve the oldest matching document
        return self.get_one(extra_filter=query, earliest=True)

    def get_latest_model_id_for_inference(
        self,
        model_status_filter: ModelStatusFilter = ModelStatusFilter.IMPROVED,
    ) -> ID:
        """
        Get the ID of the MO FP32 with XAI head version of the latest base framework model.
        This model is used for inference.

        :return: The MO model or :class:`~iai_core_py.entities.model.NullModel` if not found
        """
        # Get the ID of the latest base framework model
        base_model_id = self._get_latest_model_id_by_status(model_status_filter=model_status_filter)
        if base_model_id == ID():
            return ID()

        # Use the base model ID to search for the MO model
        aggr_pipeline = [
            {
                "$match": self.__get_latest_model_for_inference_query(
                    base_model_id=base_model_id, model_status_filter=model_status_filter
                ),
            },
            {"$project": {"_id": 1}},
        ]
        matched_docs = list(self.aggregate_read(aggr_pipeline))
        if not matched_docs:
            return ID()
        return IDToMongo.backward(matched_docs[0]["_id"])

    def update_model_status(self, model: Model, model_status: ModelStatus) -> None:
        """
        Updates the model status.

        Note: both the model instance and the database are updated.

        :param model: the model to update
        :param model_status: the new status for the model
        """
        model.model_status = model_status

        model_filter = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        model_filter["_id"] = IDToMongo.forward(model.id_)
        self._collection.update_one(filter=model_filter, update={"$set": {"model_status": model_status.name}})

    def update_training_duration(self, model: Model, training_duration: float) -> None:
        """
        Updates the model training duration. The training duration refers exclusively
        to the runtime of the model training.

        Note: both the model instance and the database are updated.

        :param model: the model to update
        :param training_duration: the new training duration to save in the database
        """
        model.training_duration = training_duration

        model_filter = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        model_filter["_id"] = IDToMongo.forward(model.id_)
        self._collection.update_one(filter=model_filter, update={"$set": {"training_duration": training_duration}})

    def update_training_job_duration(self, model: Model, training_job_duration: float) -> None:
        """
        Updates the training job duration given the model. The training job duration
        refers to the runtime of the entire training process. This includes the model
        training duration and additional steps such as evaluation and inference.

        Note: both the model instance and the database are updated.

        :param model: the model to update
        :param training_job_duration: the new training job duration to save in the database
        """
        model.training_job_duration = training_job_duration

        model_filter = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        model_filter["_id"] = IDToMongo.forward(model.id_)
        self._collection.update_one(
            filter=model_filter, update={"$set": {"training_job_duration": training_job_duration}}
        )

    def delete_by_id(self, id_: ID) -> bool:
        """
        Delete a model and its binary data (weights, exportable code) from the database
        and filesystem.

        :param id_: ID of the model to delete
        :return: True if any DB document was matched and deleted, False otherwise
        """
        # Get the document (which contains the binary data filenames). If not found, it means
        # the ID is invalid, the model was already removed, or the user can't access it
        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)
        query["_id"] = IDToMongo.forward(id_)
        model_doc = self._collection.find_one(query)
        if not model_doc:
            logger.warning(
                "Model document with id '%s' not found, possibly it is already deleted",
                id_,
            )
            return False

        # Delete the model document first, to prevent data corruption in case of error
        # during the binary deletion stage
        model_deleted: bool = super().delete_by_id(id_)

        if model_deleted:
            # Delete all the weights
            for weight_name, weight_filename in model_doc["weight_paths"]:
                logger.debug("Deleting weight file `%s` for model with ID `%s`", weight_name, id_)
                self.binary_repo.delete_by_filename(weight_filename)
            # Delete exportable code, if present
            exportable_code_filename = model_doc["exportable_code_path"]
            if exportable_code_filename:
                self.binary_repo.delete_by_filename(exportable_code_filename)

        return model_deleted

    def delete_all(self, extra_filter: dict | None = None) -> bool:
        """
        Delete all the models and their binary data (weights, exportable code).

        :param extra_filter: Optional filter to apply in addition to the default one,
            which depends on the repo type.
        :return: True if any DB document was matched and deleted, False otherwise
        """
        if extra_filter is not None:
            # Since it's not possible to apply the filter to binary repos,
            # we would need a fallback implementation that deletes matched items
            # one by one, which is much slower of course.
            raise NotImplementedError(
                "Filtering is unavailable because it is not currently possible to implement it efficiently"
            )

        # Delete the model documents first, to prevent data corruption in case of error
        # during the binaries deletion stage
        any_item_deleted = super().delete_all()

        if any_item_deleted:
            # Delete binary data (weights and exportable code)
            self.binary_repo.delete_all()

        return any_item_deleted

    def set_purge_info(self, model: Model) -> None:
        """
        Updates only the model purge info in the database.

        :param model: Model
        """
        model_filter = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        model_filter["_id"] = IDToMongo.forward(model.id_)
        purge_info_dict = ModelPurgeInfoToMongo.forward(model.purge_info)
        self._collection.update_one(filter=model_filter, update={"$set": {"purge_info": purge_info_dict}})

    def get_non_purged_base_models(self) -> list[Model]:
        """
        Gets all the base models which are not already purged. Returned models are sorted by incrementing version number

        :return: List of models, sorted by incrementing version number
        """
        query = {
            "model_format": ModelFormat.BASE_FRAMEWORK.name,
            "purge_info.is_purged": False,
            "model_status": {"$in": ModelStatusFilter.TRAINED.value},
        }
        return list(self.get_all(extra_filter=query, sort_info=[("version", 1)]))
