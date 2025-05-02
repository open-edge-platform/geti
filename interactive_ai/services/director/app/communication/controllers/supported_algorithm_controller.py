# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging
from typing import Any

from communication.views.model_template_rest_views import ModelTemplateRESTViews

from geti_telemetry_tools import unified_tracing
from iai_core.algorithms import ModelTemplateList
from iai_core.entities.model_template import ModelTemplateDeprecationStatus, TaskType

logger = logging.getLogger(__name__)


class SupportedAlgorithmRESTController:
    @staticmethod
    @unified_tracing
    def get_supported_algorithms(task_types: set[TaskType], include_obsolete: bool = True) -> dict[str, Any]:
        """
        Get all supported algorithms and default algorithms for a one or more task types.

        :param task_types: Set of task types for which to find the algorithms
        :param include_obsolete: If True, include obsolete (no longer supported) algorithms
        :return: Rest view containing the supported algorithms and default algorithms
        """
        supported_model_templates = [
            model_template
            for model_template in ModelTemplateList().get_all()
            if (
                model_template.task_type in task_types
                and (model_template.model_status is not ModelTemplateDeprecationStatus.OBSOLETE or include_obsolete)
            )
        ]
        supported_algorithms_rest = [
            ModelTemplateRESTViews.model_template_to_rest(model_template=model_template)
            for model_template in supported_model_templates
        ]
        return {
            "supported_algorithms": supported_algorithms_rest,
        }
