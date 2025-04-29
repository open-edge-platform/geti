# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

import pytest

from communication.controllers.supported_algorithm_controller import SupportedAlgorithmRESTController
from communication.views.model_template_rest_views import ModelTemplateRESTViews

from sc_sdk.algorithms import ModelTemplateList
from sc_sdk.entities.model_template import TaskType


class TestSupportedAlgorithmRESTController:
    @pytest.mark.parametrize("include_obsolete", [True, False])
    def test_get_supported_algorithms(
        self, fxt_model_template_segmentation, fxt_model_template_obsolete, include_obsolete
    ) -> None:
        supported_algorithm_rest = {"key": "value"}
        with (
            patch.object(
                ModelTemplateList,
                "get_all",
                return_value=[fxt_model_template_segmentation, fxt_model_template_obsolete],
            ) as mock_get_templates,
            patch.object(
                ModelTemplateRESTViews, "model_template_to_rest", return_value=supported_algorithm_rest
            ) as mock_to_rest,
        ):
            result = SupportedAlgorithmRESTController.get_supported_algorithms(
                task_types={TaskType.SEGMENTATION}, include_obsolete=include_obsolete
            )

        mock_get_templates.assert_called_once_with()
        assert mock_to_rest.call_count == 2 if include_obsolete else 1
        expected_algos = [supported_algorithm_rest] * (2 if include_obsolete else 1)
        assert result == {"supported_algorithms": expected_algos}
