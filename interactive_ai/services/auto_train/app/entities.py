# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Entities used by the auto-train controller"""

from datetime import datetime
from enum import Enum, auto

from geti_types import ID, ProjectIdentifier, Session, make_session, PersistentEntity


class FeatureFlag(Enum):
    FEATURE_FLAG_CREDIT_SYSTEM = auto()
    FEATURE_FLAG_RETAIN_TRAINING_ARTIFACTS = auto()


class AutoTrainActivationRequest(PersistentEntity):
    """
    AutoTrainActivationRequest represents a potential deferred request
    to trigger auto-train on a task.

    :param project_id: ID of the project containing the task
    :param task_node_id: ID of the task node
    :param model_storage_id: ID of the model storage to use in the training job
    :param timestamp: Timestamp associated with the request; the auto-training job
        shall not start earlier than this timestamp plus a predetermined interval
    :param ready: Whether the task is considered ready for auto-training
    :param bypass_debouncer: If True and the task is ready for auto-training, then
        the request will be processed asap without applying any debouncing period
    :param session: Session associated with the request
    """

    def __init__(  # noqa: PLR0913
        self,
        project_id: ID,
        task_node_id: ID,
        timestamp: datetime,
        ready: bool,
        bypass_debouncer: bool,
        session: Session,
        model_storage_id: ID | None = None,
        ephemeral: bool = True,
    ):
        super().__init__(id_=task_node_id, ephemeral=ephemeral)
        self.project_id = project_id
        self.model_storage_id = model_storage_id
        self.timestamp = timestamp
        self.ready = ready
        self.bypass_debouncer = bypass_debouncer
        self.session = session

    @property
    def task_node_id(self) -> ID:
        """Get the ID of the task node"""
        return self.id_

    @property
    def workspace_id(self) -> ID:
        """Get the ID of the workspace"""
        return self.session.workspace_id

    @property
    def project_identifier(self) -> ProjectIdentifier:
        """Get the project identifier"""
        return ProjectIdentifier(project_id=self.project_id, workspace_id=self.workspace_id)


class NullAutoTrainActivationRequest(AutoTrainActivationRequest):
    """Representation of a not found request"""

    def __init__(self) -> None:
        super().__init__(
            project_id=ID(),
            task_node_id=ID(),
            model_storage_id=ID(),
            timestamp=datetime.fromtimestamp(0),
            ready=False,
            bypass_debouncer=False,
            session=make_session(),
        )
