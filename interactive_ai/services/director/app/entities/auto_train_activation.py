# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the AutoTrainActivation"""

from datetime import datetime

from geti_types import ID, Session, make_session, PersistentEntity
from iai_core.utils.time_utils import now


class AutoTrainActivation(PersistentEntity):
    """
    AutoTrainActivation is used to trigger the auto-training feature for a trainable task node.

    An AutoTrainActivation represents a "potential deferred request to auto-train", i.e. a way to
    signal that an auto-train job should be submitted not earlier than a certain timestamp (deferred)
    if and only if the auto-train conditions are satisfied (potential).

    AutoTrainActivation uses the same ID of the corresponding task node, which makes it
    a per task node singleton from the logical point of view.

    :param task_node_id: ID of the task node, also used as ID for the AutoTrainActivation object
    :param session: Session associated with the event that stimulated the auto-train mechanism
    :param model_storage_id: ID of the model storage with the trained model for the task.
    :param ready: Whether the task is deemed ready for auto-train after checking the conditions. Defaults to False.
    :param request_time: Timestamp of the event that may potentially cause auto-training to be triggered.
        If not provided, the current timestamp is used as default.
    """

    def __init__(
        self,
        task_node_id: ID,
        session: Session,
        model_storage_id: ID | None = None,
        ready: bool = False,
        request_time: datetime | None = None,
        ephemeral: bool = True,
    ) -> None:
        super().__init__(id_=task_node_id, ephemeral=ephemeral)
        self.model_storage_id = model_storage_id
        self.session = session
        self.ready = ready
        self.request_time = request_time if request_time else now()

    @property
    def task_node_id(self) -> ID:
        """Returns the corresponding task node ID"""
        return self.id_

    def __eq__(self, other: object):
        if not isinstance(other, AutoTrainActivation):
            return False
        return self.id_ == other.id_ and self.ready == other.ready and self.request_time == self.request_time

    def __repr__(self):
        """
        Returns the string representation of the AutoTrainActivation instance (only basic info is included)
        """
        return (
            f"{self.__class__.__name__}(task_node_id={self.task_node_id}"
            f", ready='{self.ready}'"
            f", request_time='{self.request_time}'"
        )


class NullAutoTrainActivation(AutoTrainActivation):
    def __init__(self) -> None:
        super().__init__(task_node_id=ID(), session=make_session())
