# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

"""
This module contains the ComponentRegisterEntry class, which is used to add component
configurations into the ComponentRegistry
"""

from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters
from sc_sdk.entities.model_template import TaskType


class ComponentRegisterEntry:
    """
    This class is used in the ConfigurableComponentRegister. It contains configuration types for
    different types of tasks.
    """

    def __init__(
        self,
        default_type: type[ConfigurableParameters],
        classification_type: type[ConfigurableParameters] | None = None,
        anomaly_type: type[ConfigurableParameters] | None = None,
        keypoint_type: type[ConfigurableParameters] | None = None,
    ) -> None:
        self._default_type = default_type
        self._classification_type = classification_type
        self._anomaly_type = anomaly_type
        self._keypoint_type = keypoint_type

    def get_configuration_type(self, task_type: TaskType | None = None) -> type[ConfigurableParameters]:
        """
        Returns the configuration type. A certain `task_type` can be passed to
        retrieve the configuration type to use for that kind of task.

        :param task_type: TaskType to retrieve the configuration type for. Defaults to
            None, in which case this method returns the default configuration type for
            the Component
        :return: Type of the configuration for this task_type
        """
        result: type[ConfigurableParameters] = self._default_type
        if task_type is not None:
            if task_type.is_anomaly and self._anomaly_type is not None:
                result = self._anomaly_type
            if task_type == TaskType.CLASSIFICATION and self._classification_type is not None:
                result = self._classification_type
            if task_type == TaskType.KEYPOINT_DETECTION and self._keypoint_type is not None:
                result = self._keypoint_type
        return result
