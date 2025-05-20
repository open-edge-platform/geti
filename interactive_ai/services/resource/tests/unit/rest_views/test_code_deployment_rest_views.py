# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from testfixtures import compare

from communication.rest_views.code_deployment_rest_views import CodeDeploymentRestViews


class TestCodeDeploymentRESTViews:
    def test_code_deployment_to_rest(self, fxt_code_deployment_rest, fxt_code_deployment):
        result = CodeDeploymentRestViews.to_rest(code_deployment=fxt_code_deployment)

        compare(result, fxt_code_deployment_rest, ignore_eq=True)
