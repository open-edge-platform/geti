# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the ICommand abstract interface class."""

import abc
import logging

from bson import ObjectId
from geti_types import ID

logger = logging.getLogger(__name__)


class ICommand(metaclass=abc.ABCMeta):
    """
    Interface class for Commands to be executed as part of a Job.
    """

    __id: ID
    # step_count is used to weight the command for visual reporting purposes.
    # Set it to 0 for short or not-so-important commands, so that completing such
    # commands is not shown as a step advancement in the overall progress.
    # On the contrary, set it to 1 or more to include this command in the step counting.
    step_count: int = 0

    def __init__(self) -> None:
        self.id_ = ID(ObjectId())
        self.cancelled = False

    @property
    def id_(self) -> ID:
        """ID of the command"""
        return self.__id

    @id_.setter
    def id_(self, value: ID):
        self.__id = value

    @abc.abstractmethod
    def execute(self) -> None:
        """
        Execute the command.

        :raises CommandFailedException: if the command fails to execute
        """

    def cancel(self) -> None:
        """Cancel the command."""
        logger.warning(
            f"{self.__class__.__name__} cannot be cancelled. This command will carry on until finished. "
            "After this command is finished, the job will be cancelled."
        )

    def revert_command(self) -> None:
        """Callback to run upon command cancellation."""
        logger.debug(f"Command of type '{self.__class__.__name__}' does not implement revert_command() method")

    def get_message(self) -> str:
        """
        :return: short message explaining what the command does
        """
        return ""

    def get_progress(self) -> float:
        """
        :return: progress as a float between 0 and 100, -1.0 if progress not applicable
        """
        return -1.0

    def get_current_step_index(self) -> int:
        """
        Get the index of the current step in the command, 1-indexed.

        Multi-step commands should override this method to always reflect the
        current progress of the command in terms of step.
        The output must be in range [1, step_count]

        :return: index of the current step in the command
        """
        return 1

    def clear(self):  # noqa: ANN201
        """
        Called to free any resources (include outputs) left by the command
        """


class NullCommand(ICommand):
    """Dummy command."""

    def execute(self) -> None:
        logger.error("Attempted to execute NullCommand, which is not executable.")
