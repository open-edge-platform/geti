# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from testfixtures import compare

from communication.views.model_template_rest_views import ModelTemplateRESTViews


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
