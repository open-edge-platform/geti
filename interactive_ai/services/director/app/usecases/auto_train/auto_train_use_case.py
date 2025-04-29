# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


"""
This module contains the AutoTrainUseCase, that checks the dataset counter to determine whether the project
should be auto-trained.
"""

import logging
import os
from threading import Thread
from typing import TYPE_CHECKING

from rx.operators import debounce
from rx.scheduler import EventLoopScheduler
from rx.subject import Subject

from coordination.configuration_manager.task_node_config import AnomalyTaskNodeConfig, TaskNodeConfig
from coordination.dataset_manager.missing_annotations_helper import MissingAnnotationsHelper
from entities.auto_train_activation import AutoTrainActivation
from storage.repos.auto_train_activation_repo import ProjectBasedAutoTrainActivationRepo

from geti_telemetry_tools import unified_tracing
from geti_types import (
    CTX_SESSION_VAR,
    DatasetStorageIdentifier,
    ProjectIdentifier,
    RequestSource,
    Session,
    session_context,
)
from sc_sdk.configuration.elements.component_parameters import ComponentType
from sc_sdk.entities.project import Project
from sc_sdk.entities.task_node import TaskNode
from sc_sdk.repos import ConfigurableParametersRepo, ProjectRepo, TaskNodeRepo

if TYPE_CHECKING:
    from geti_types import ID

AUTO_TRAIN_AUTHOR = "geti"
logger = logging.getLogger(__name__)


class AutoTrainUseCase:
    """
    This class is responsible for checking whether a project should be auto-trained. To check this, it interacts with
    the MissingAnnotationsHelper and the configuration. In case the project is ready to be trained,
    it is also responsible for creating the auto-training jobs.

    When mass annotations come in, auto-training needs to be postponed to the last annotation. To make sure of that,
    we use a debouncer. (https://rxpy.readthedocs.io/en/latest/reference_operators.html#rx.operators.debounce)
    """

    def __init__(self) -> None:
        # todo: CVS-85274 Make the debouncer crash-proof
        self.__debouncer_schedulers: dict[ID, EventLoopScheduler] = {}
        self.__subjects: dict[ID, Subject] = {}
        self._auto_train_debounce_time = float(os.environ.get("AUTO_TRAIN_DEBOUNCE_TIME", "5"))

    @property
    def auto_train_debounce_time(self) -> float:
        return self._auto_train_debounce_time

    def stop(self) -> None:
        """Dispose all of the debouncer's schedulers"""
        for scheduler in self.__debouncer_schedulers.values():
            scheduler.dispose()

    @staticmethod
    def on_configuration_changed(project_identifier: ProjectIdentifier) -> None:
        """
        Handler for when the configuration changes in a project.

        Action: check if the project is ready for auto-training, since the configuration update may affect
        the readiness conditions.

        :param project_identifier: Identifier of the project where the model was trained
        """
        AutoTrainUseCase._check_conditions_and_set_auto_train_readiness(project_identifier=project_identifier)

    def on_dataset_counters_updated(self, project_identifier: ProjectIdentifier) -> None:
        """
        Handler for when the dataset counters are updated in a project after processing new annotations.

        Action: check if the project is ready for training, since the number of annotations may now be sufficient
        for auto-training. Requests submitted via API key are subject to a debouncing mechanism that prevents
        auto-training from triggering too early in case of bulk annotations.

        :param project_identifier: Identifier of the project where the annotation is added
        """
        session = CTX_SESSION_VAR.get()
        is_labeled_media_upload = session.extra.get("labeled_media_upload", "").lower() == "true"
        AutoTrainUseCase.upsert_auto_train_request_timestamps_for_tasks(project_identifier=project_identifier)
        logger.debug(
            f"AutoTrainUseCase: processing dataset counters updated for {project_identifier}. "
            f"source={session.source}, is_labeled_media_upload={is_labeled_media_upload}"
        )
        match session.source:
            case RequestSource.INTERNAL:
                # Assumption: the dataset was updated in a job, either dataset import or training dataset preparation.
                # In both cases, auto-training should not start.
                return
            case RequestSource.API_KEY:
                # API_KEY requests typically come from the SDK, which may upload annotations at a high rate:
                # apply a debouncing period to avoid overloading the director MS.
                self._check_conditions_and_set_auto_train_readiness_debounce(project_identifier=project_identifier)
            case RequestSource.BROWSER | RequestSource.UNKNOWN:
                # For all other requests, with the only exception of labeled media upload, check readiness right away
                if is_labeled_media_upload:
                    self._check_conditions_and_set_auto_train_readiness_debounce(project_identifier=project_identifier)
                else:
                    self._check_conditions_and_set_auto_train_readiness(project_identifier=project_identifier)
            case _:
                raise ValueError(f"Unsupported source: {session.source}")

    @staticmethod
    def on_training_successful(project_identifier: ProjectIdentifier) -> None:
        """
        Handler for when a model is successfully trained in a project.

        Action: check if the project is ready for another round of training. Typically, this happens when new
        annotations are added while the model was training.

        :param project_identifier: Identifier of the project where the model was trained
        """
        AutoTrainUseCase._check_conditions_and_set_auto_train_readiness(project_identifier=project_identifier)

    @unified_tracing
    def _check_conditions_and_set_auto_train_readiness_debounce(self, project_identifier: ProjectIdentifier) -> None:
        """
        Buffer auto-train checking using debounce. Only execute the event handler after 5 seconds of absence
        of signal. This is done so that when mass annotations come in, we only check auto-train after all the
        annotations are received. More information:
        https://rxpy.readthedocs.io/en/latest/reference_operators.html#rx.operators.debounce

        :param project_identifier: Identifier of the project for which auto-train is checked
        """
        session = CTX_SESSION_VAR.get()
        if project_identifier.project_id not in self.__debouncer_schedulers:
            scheduler = EventLoopScheduler(
                lambda target: Thread(
                    target=target, daemon=True, name=f"Debounce scheduler for project {project_identifier.project_id}"
                )
            )
            subject = Subject()

            self.__debouncer_schedulers[project_identifier.project_id] = scheduler
            self.__subjects[project_identifier.project_id] = subject
            debouncer = debounce(self.auto_train_debounce_time, scheduler=scheduler)
            debouncer(subject).subscribe(
                lambda _: AutoTrainUseCase._check_conditions_and_set_auto_train_readiness(
                    project_identifier=project_identifier,
                    bypass_debouncer=False,
                    session=session,  # session must be passed explicitly since the debounced fn runs in another thread
                )
            )
        self.__subjects[project_identifier.project_id].on_next(None)

    @staticmethod
    @unified_tracing
    def _check_conditions_and_set_auto_train_readiness(
        project_identifier: ProjectIdentifier, bypass_debouncer: bool = True, session: Session | None = None
    ) -> None:
        """
        Check whether auto-training is enabled and if any task is ready for it, then update
        the readiness status accordingly.

        :param project_identifier: Identifier of the Project to update the dataset counter for
        :param bypass_debouncer: If True, no debouncing period is applied to process the auto-train request when ready
        :param session: Session object; if unspecified, uses the global session
        """
        if session is None:
            session = CTX_SESSION_VAR.get()
        with session_context(session=session):
            project = ProjectRepo().get_by_id(project_identifier.project_id)
            trainable_tasks_ids = [tn.id_ for tn in project.get_trainable_task_nodes()]
            auto_train_activation_repo = ProjectBasedAutoTrainActivationRepo(project_identifier=project_identifier)

            auto_train_ready_tasks_ids = [
                tn.id_ for tn in AutoTrainUseCase.__get_auto_train_ready_tasks(project=project)
            ]
            for task_node_id in trainable_tasks_ids:
                ready_to_auto_train = task_node_id in auto_train_ready_tasks_ids
                if ready_to_auto_train:
                    logger.info(
                        "Task '%s' of project '%s' is now ready for auto-training.",
                        task_node_id,
                        project.name,
                    )
                try:
                    auto_train_activation_repo.set_auto_train_readiness_by_task_id(
                        task_node_id=task_node_id,
                        readiness=ready_to_auto_train,
                        bypass_debouncer=bypass_debouncer,
                        # When no debouncing is applied, the document is processed and removed immediately
                        # so it is possible that it cannot be found. If so, just continue without raising an error.
                        raise_exc_on_missing=(not bypass_debouncer),
                    )
                except ValueError:
                    logger.warning(
                        "Failed to set auto-train readiness for task '%s'. Skipping it.",
                        task_node_id,
                        exc_info=True,
                    )

    @staticmethod
    def __is_auto_train_enabled_for_task(project_identifier: ProjectIdentifier, task_node: TaskNode) -> bool:
        """
        Checks whether auto-training is enabled for a particular task node.

        :param project_identifier: The identifier of the project containing the task node
        :param task_node: The task node to check
        :returns: True if auto-training is enabled for the task node, False otherwise.
        """
        task_configuration_type = AnomalyTaskNodeConfig if task_node.task_properties.is_anomaly else TaskNodeConfig
        task_configuration = ConfigurableParametersRepo(project_identifier).get_or_create_component_parameters(
            data_instance_of=task_configuration_type,
            task_id=task_node.id_,
            component=ComponentType.TASK_NODE,
        )
        return task_configuration.auto_training

    @classmethod
    def __get_auto_train_ready_tasks(
        cls,
        project: Project,
    ) -> list[TaskNode]:
        """
        Checks which tasks are ready to be trained and returns a list containing all auto-train ready tasks. This
        method checks three conditions:
         - Auto-train is enabled for the task
         - The number of required annotations is met for the task

        :param project: Project for which auto-train ready tasks are computed
        :return: the list of the tasks that are ready to be trained.
        """
        training_dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=project.training_dataset_storage_id,
        )
        output: list[TaskNode] = []
        for task_node in project.get_trainable_task_nodes():
            missing_annotations = MissingAnnotationsHelper.get_missing_annotations_for_task(
                dataset_storage_identifier=training_dataset_storage_identifier,
                task_node=task_node,
            )
            required_annotations_met = missing_annotations.total_missing_annotations_auto_training <= 0

            auto_train_enabled = cls.__is_auto_train_enabled_for_task(
                project_identifier=project.identifier, task_node=task_node
            )
            if required_annotations_met and auto_train_enabled:
                output.append(task_node)
        return output

    @staticmethod
    @unified_tracing
    def upsert_auto_train_request_timestamps_for_tasks(project_identifier: ProjectIdentifier) -> None:
        """
        When the dataset counter is updated, upsert an AutoTrainActivation for each trainable task in the project.

        :param project_identifier: Identifier of the project related to the dataset counter update event
        """
        session = CTX_SESSION_VAR.get()
        autotrain_activation_repo = ProjectBasedAutoTrainActivationRepo(project_identifier)
        task_node_repo = TaskNodeRepo(project_identifier)
        for task_node_id in task_node_repo.get_trainable_task_ids():
            auto_train_activation = AutoTrainActivation(task_node_id=task_node_id, session=session)
            autotrain_activation_repo.upsert_timestamp_for_task(instance=auto_train_activation)
