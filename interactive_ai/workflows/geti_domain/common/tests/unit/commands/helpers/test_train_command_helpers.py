# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import patch

import pytest
from _pytest.fixtures import FixtureRequest
from sc_sdk.repos import ModelRepo
from sc_sdk.repos.model_repo import ModelStatusFilter
from testfixtures import compare

from jobs_common.jobs.helpers.model_helpers import select_input_model


def return_none(*args, **kwargs) -> None:
    return None


@pytest.mark.JobsComponent
@patch.object(ModelRepo, "__init__", new=return_none)
class TestTrainCommandHelpers:
    @pytest.mark.parametrize(
        "lazyfxt_model, from_scratch, expected_return",
        [
            ("fxt_model", False, True),
            ("fxt_null_model", False, None),
            ("fxt_obsolete_model", False, None),
            ("fxt_model", True, None),
            ("fxt_null_model", True, None),
            ("fxt_obsolete_model", True, None),
        ],
        ids=[
            "Previous model, not from scratch",
            "No previous model, not from scratch",
            "Obsolete model, not from scratch",
            "Previous model, from scratch",
            "No previous model, from scratch",
            "Obsolete model, from scratch",
        ],
    )
    def test_select_input_model(
        self,
        lazyfxt_model,
        from_scratch,
        expected_return,
        fxt_model_storage,
        request: FixtureRequest,
    ):
        # Arrange
        fxt_model = request.getfixturevalue(lazyfxt_model)
        if expected_return is not None:
            expected_return = fxt_model

        # Act
        with patch.object(ModelRepo, "get_latest", return_value=fxt_model) as mock_get_latest:
            model = select_input_model(model_storage=fxt_model_storage, from_scratch=from_scratch)

        # Assert
        if not from_scratch:
            mock_get_latest.assert_called_once_with(
                model_status_filter=ModelStatusFilter.IMPROVED,
                include_optimized_models=False,
            )
        compare(model, expected_return, ignore_eq=True)
