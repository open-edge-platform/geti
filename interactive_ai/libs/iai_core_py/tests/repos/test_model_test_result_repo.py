#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#


from iai_core_py.entities.model_test_result import NullModelTestResult
from iai_core_py.repos import ModelTestResultRepo


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
