# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines the command to update the active model"""

import logging

from iai_core.entities.model_storage import ModelStorage
from iai_core.entities.task_node import TaskNode
from iai_core.services.model_service import ModelService
from jobs_common.commands.interfaces.command import ICommand

logger = logging.getLogger(__name__)


class UpdateActiveModelCommand(ICommand):
    """
    Command to update the active model of a task.

    :param task_node: Task node to update
    :param new_model_storage: Model storage to set as the active one
    """

    def __init__(
        self,
        task_node: TaskNode,
        new_model_storage: ModelStorage,
    ) -> None:
        super().__init__()
        self.task_node = task_node
        self.new_model_storage = new_model_storage
        self.old_model_storage = ModelService.get_active_model_storage(
            project_identifier=new_model_storage.project_identifier,
            task_node_id=task_node.id_,
        )

    def _set_active_model_storage(self, model_storage: ModelStorage):
        logger.info(
            "Updating active model storage to %s for task %s (ID %s)",
            model_storage.model_template.model_template_id,
            self.task_node.title,
            self.task_node.id_,
        )
        ModelService.activate_model_storage(model_storage=model_storage)

    def execute(self) -> None:
        """Update the active model storage."""
        if self.new_model_storage.id_ != self.old_model_storage.id_:
            self._set_active_model_storage(model_storage=self.new_model_storage)

    def revert_command(self) -> None:
        """
        Restore the previous active model
        """
        if self.new_model_storage.id_ != self.old_model_storage.id_:
            self._set_active_model_storage(model_storage=self.old_model_storage)

    def get_message(self) -> str:
        """
        :return: short message explaining what the command does
        """
        return "Updating the active model for the task"
