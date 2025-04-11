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


from testfixtures import compare

from communication.views.model_template_rest_views import ModelTemplateRESTViews
from features.feature_flag_provider import FeatureFlag


class TestSCModelTemplateRESTViews:
    def test_model_template_to_rest(self, fxt_model_template_classification) -> None:
        expected_result = {
            "name": fxt_model_template_classification.name,
            "task_type": fxt_model_template_classification.task_type.name.lower(),
            "model_size": fxt_model_template_classification.size,
            "model_template_id": fxt_model_template_classification.model_template_id,
            "gigaflops": fxt_model_template_classification.gigaflops,
            "summary": fxt_model_template_classification.summary,
            "supports_auto_hpo": False,
            "default_algorithm": True,
            "performance_category": fxt_model_template_classification.model_category.name.lower(),
            "lifecycle_stage": fxt_model_template_classification.model_status.name.lower(),
        }

        result = ModelTemplateRESTViews.model_template_to_rest(model_template=fxt_model_template_classification)

        compare(result, expected_result, ignore_eq=True)

    def test_model_template_to_rest_with_reduced_anomaly(
        self,
        fxt_model_template_anomaly_detection,
        fxt_enable_feature_flag_name,
    ) -> None:
        fxt_enable_feature_flag_name(FeatureFlag.FEATURE_FLAG_ANOMALY_REDUCTION.name)
        expected_result = {
            "name": fxt_model_template_anomaly_detection.name,
            "task_type": "anomaly",
            "model_size": fxt_model_template_anomaly_detection.size,
            "model_template_id": fxt_model_template_anomaly_detection.model_template_id,
            "gigaflops": fxt_model_template_anomaly_detection.gigaflops,
            "summary": fxt_model_template_anomaly_detection.summary,
            "supports_auto_hpo": False,
            "default_algorithm": False,
            "performance_category": fxt_model_template_anomaly_detection.model_category.name.lower(),
            "lifecycle_stage": fxt_model_template_anomaly_detection.model_status.name.lower(),
        }

        result = ModelTemplateRESTViews.model_template_to_rest(model_template=fxt_model_template_anomaly_detection)

        compare(result, expected_result, ignore_eq=True)
