# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

"""This module defines base create dataset command"""

import logging
from abc import ABCMeta, abstractmethod

from sc_sdk.entities.dataset_storage import DatasetStorage
from sc_sdk.entities.project import Project

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
