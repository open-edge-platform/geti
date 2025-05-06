# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This file defines the ModelTemplateList class"""

import glob
import os
import pathlib
import time
from dataclasses import dataclass
from threading import Lock

from sc_sdk.entities.model_template import (
    ModelTemplate,
    ModelTemplateDeprecationStatus,
    NullModelTemplate,
    parse_model_template,
    parse_model_template_from_dict,
)

from .algorithm import Algorithm, AlgorithmStats, NullAlgorithm, SupportedStatus
from .hyperparameters import (
    AugmentationParameters,
    DatasetPreparationParameters,
    EvaluationParameters,
    Hyperparameters,
    TrainingHyperParameters,
)
from geti_types import Singleton

__all__ = [
    "Algorithm",
    "AlgorithmStats",
    "AugmentationParameters",
    "DatasetPreparationParameters",
    "EvaluationParameters",
    "Hyperparameters",
    "NullAlgorithm",
    "SupportedStatus",
    "TrainingHyperParameters",
]


class ModelTemplateList(metaclass=Singleton):
    """
    Singleton task containing the list of model templates available to the system.

    The list of model templates is read from a director specified by the env. var. MODEL_TEMPLATES_DIR.
    If the director is modified, the model templates will be automatically reloaded from disk.
    """

    @dataclass
    class Entry:
        """
        Entry representing a model template.

        :var model_template: The deserialised model template
        :var location: Location in the model templates directory
        :var mtime: Last modification time of the file; ``None`` if the model template is not backed by a file
        """

        model_template: ModelTemplate
        location: str | None = None
        mtime: float | None = None

    def __init__(self) -> None:
        self._model_template_list: dict[str, ModelTemplateList.Entry] = {}
        base_dirs: list = __path__  # type: ignore[name-defined]
        # 'model_templates_dir' is assumed to point to one directory only
        model_templates_dir: str | None = os.getenv("MODEL_TEMPLATES_DIR")
        if model_templates_dir:
            base_dirs.append(model_templates_dir)

        self._base_dirs = base_dirs
        self._location_to_id_: dict[str, str] = {}
        self._update_lock = Lock()
        self._model_template_list_last_updated = 0
        self._obsolete_model_template_ids: set[str] = set()

        # Warmup the cache
        self._update_model_template_list()

    @staticmethod
    def _update_entry_if_needed(entry: "ModelTemplateList.Entry") -> None:
        """
        Update an entry if needed
        """
        mtime: float | None = None
        file_path: pathlib.Path | None = None

        try:
            if entry.location is not None:
                file_path = pathlib.Path(entry.location)

                mtime = file_path.stat().st_mtime
        except FileNotFoundError:
            # In this case, we assume that the file was manually registered and is not backed by any file.
            # This is typically used during testing.
            pass

        if file_path is not None and mtime != entry.mtime:
            entry.model_template = parse_model_template(str(file_path))
            entry.mtime = mtime

    def _update_model_template_list(self):
        """
        Update the list of all model templates.
        """
        with self._update_lock:
            # Update no more than every 10s to avoid performance issues.
            minimum_duration_between_updates = 10
            current_time = int(time.time())

            if current_time < self._model_template_list_last_updated + minimum_duration_between_updates:
                return

            self._model_template_list_last_updated = current_time

            new_model_template_list: dict[str, ModelTemplateList.Entry] = {}
            new_location_to_id: dict[str, str] = {}

            for base_dir in self._base_dirs:
                glob_path = os.path.join(base_dir, "**", "template.yaml")
                file_list = glob.glob(glob_path, recursive=True)

                for location in file_list:
                    model_template_id = self._location_to_id_.get(location, None)
                    if model_template_id is None or model_template_id not in self._model_template_list:
                        entry = ModelTemplateList.Entry(NullModelTemplate(), location)
                    else:
                        entry = self._model_template_list[model_template_id]
                        if entry.location is None:
                            # If the location in the entry is None, this means that
                            # this template was overridden using register_model_template()
                            # This happens in some of the tests.
                            continue

                    self._update_entry_if_needed(entry)
                    model_template_id = entry.model_template.model_template_id
                    new_location_to_id[location] = model_template_id
                    new_model_template_list[model_template_id] = entry
                    if entry.model_template.model_status is ModelTemplateDeprecationStatus.OBSOLETE:
                        self._obsolete_model_template_ids.add(model_template_id)

            # During testing, some model templates might have been registered directly without being backed by a file
            # Append those as well.
            # Note that we ignore the NULL task type which corresponds to the NullModelTemplate.
            for id_, entry in self._model_template_list.items():
                if entry.mtime is None:
                    new_model_template_list[id_] = entry

            self._model_template_list = new_model_template_list
            self._location_to_id_ = new_location_to_id

    @property
    def obsolete_model_template_ids(self) -> set[str]:
        """
        Get the ids of the obsolete model templates

        :return: A set of model template ids that are obsolete
        """
        return self._obsolete_model_template_ids

    def get_all_ids(self) -> list[str]:
        """
        Get a list of the IDs of all the model templates available.
        """
        self._update_model_template_list()
        return list(self._model_template_list.keys())

    def get_all(self) -> list[ModelTemplate]:
        """
        Get a list of all the model templates available.
        """
        self._update_model_template_list()
        return [entry.model_template for entry in self._model_template_list.values()]

    def get_by_id(self, model_template_id: str) -> ModelTemplate:
        """
        Get a specific model template by ID. If the model_template_id is empty, return
        a NullModelTemplate.
        """
        self._update_model_template_list()
        entry = self._model_template_list.get(model_template_id, None)
        if entry is not None and model_template_id:
            return entry.model_template
        return NullModelTemplate()

    def register_model_template(self, model_template: dict | ModelTemplate) -> ModelTemplate:
        """
        Register a new model template, so that it is accessible through this class.

        This model template will not be backed by a model template file. This function is useful to add
        model templates at runtime inside the test suite.

        :param model_template: The model template to add
        :return: The newly created model template
        """
        if isinstance(model_template, dict):
            model_template = parse_model_template_from_dict(model_template)
        self._model_template_list[model_template.model_template_id] = self.Entry(model_template)
        if model_template.model_status is ModelTemplateDeprecationStatus.OBSOLETE:
            self._obsolete_model_template_ids.add(model_template.model_template_id)

        return model_template

    def unregister_model_template(self, model_template_id: str) -> None:
        """
        Unregister a model template, so that it is no longer accessible through this class.

        This function is typically used at the end of a test inside the test suite. Note that this function
        only works with model templates added with `register_model_template()`. The other model templates
        will be automatically reloaded from the disk.

        :param model_template_id: The ID of the model template to remove
        """
        self._model_template_list.pop(model_template_id, None)
        self._obsolete_model_template_ids.discard(model_template_id)


class AlgorithmsList(metaclass=Singleton):
    """
    Singleton class containing the list of algorithms available to train.
    """

    def __init__(self) -> None:
        self._algorithms_list: dict[str, Algorithm] = {}
        base_dirs: list = __path__  # type: ignore[name-defined]
        # 'algorithms_dir' is assumed to point to one directory only
        algorithms_dir: str | None = os.getenv("ALGORITHMS_DIR")
        if algorithms_dir:
            base_dirs.append(algorithms_dir)

        self._base_dirs = base_dirs
        self._update_lock = Lock()
        self._obsolete_model_template_ids: set[str] = set()
        self._update_algorithms_list()

    @property
    def obsolete_model_template_ids(self) -> set[str]:
        """
        Get the ids of the obsolete model templates

        :return: A set of model template ids that are obsolete
        """
        return self._obsolete_model_template_ids

    def _update_algorithms_list(self) -> None:
        """
        Update the list of all available algorithms.

        This function scans the base directories for algorithm manifest files,
        loads them into Algorithm objects, and updates the internal algorithm list.
        """
        # TODO: implement when model manifest are populated
        raise NotImplementedError

    def get_by_id(self, algorithm_id: str) -> Algorithm:
        """
        Get a specific algorithm by ID. If the algorithm_id is not valid or empty, return a NullAlgorithm.
        """
        self._update_algorithms_list()
        algorithm = self._algorithms_list.get(algorithm_id)
        if algorithm is None:
            return NullAlgorithm()
        return algorithm

    def get_all_ids(self) -> list[str]:
        """
        Get a list of the IDs of all the algorithms available.
        """
        self._update_algorithms_list()
        return list(self._algorithms_list.keys())

    def get_all(self) -> list[Algorithm]:
        """
        Get a list of all the algorithms available.
        """
        self._update_algorithms_list()
        return list(self._algorithms_list.values())
