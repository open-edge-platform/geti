#
# INTEL CONFIDENTIAL
# Copyright (c) 2022 Intel Corporation
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material contains trade secrets and proprietary
# and confidential information of Intel or its suppliers and licensors. The
# Material is protected by worldwide copyright and trade secret laws and treaty
# provisions. No part of the Material may be used, copied, reproduced, modified,
# published, uploaded, posted, transmitted, distributed, or disclosed in any way
# without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
#

import pytest

from sc_sdk.entities.model_test_result import NullModelTestResult
from sc_sdk.repos import ModelTestResultRepo


@pytest.mark.ScSdkComponent
class TestModelTestResultRepo:
    def test_model_test_result_repo(self, request, fxt_model_test_result, fxt_empty_project) -> None:
        """
        <b>Description:</b>
        Check that ModelTestResultRepo behaves correctly

        <b>Input data:</b>
        ModelTestResult instance

        <b>Expected results:</b>
        Test succeeds if user test can be inserted in the database, retrieved and deleted.

        <b>Steps</b>
        1. Create Input data
        2. Add ModelTestResult to the project
        3. Retrieve the ModelTestResult and check that it is the right one
        3. Delete the ModelTestResult and check that it is deleted
        """
        model_test_result_repo = ModelTestResultRepo(fxt_empty_project.identifier)
        request.addfinalizer(lambda: model_test_result_repo.delete_by_id(fxt_model_test_result.id_))

        model_test_result_repo.save(fxt_model_test_result)

        model_test_result_back = model_test_result_repo.get_by_id(fxt_model_test_result.id_)
        assert model_test_result_back == fxt_model_test_result

        model_test_results = list(
            model_test_result_repo.get_all_by_dataset_storage_id(fxt_model_test_result.dataset_storage_ids[0])
        )
        assert model_test_results[0] == fxt_model_test_result

        model_test_result_repo.delete_by_id(fxt_model_test_result.id_)
        assert model_test_result_repo.get_by_id(fxt_model_test_result.id_) == NullModelTestResult()
