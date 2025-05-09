# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines base create dataset command"""

import logging
from abc import ABCMeta, abstractmethod

from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.project import Project

from jobs_common.commands.interfaces.command import ICommand

logger = logging.getLogger(__name__)


class CreateDatasetCommand(ICommand, metaclass=ABCMeta):
    """
    Base class for the dataset creation commands

    :param project: project containing dataset storage
    :param dataset_storage: dataset storage containing media and annotations
    """

    def __init__(self, project: Project, dataset_storage: DatasetStorage) -> None:
        super().__init__()
        self.project = project
        self.dataset_storage = dataset_storage

    @abstractmethod
    def execute(self) -> None:
        """
        Create the dataset.

        :raises DatasetCreationFailedException: if the dataset cannot be created
        """
