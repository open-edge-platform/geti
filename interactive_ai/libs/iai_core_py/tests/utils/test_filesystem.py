# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os
from unittest.mock import patch

import pytest

from iai_core.repos import BinaryRepo
from iai_core.utils.filesystem import check_free_space_for_operation, check_free_space_for_upload, compute_project_size

FEATURE_FLAG_STORAGE_SIZE_COMPUTATION = "FEATURE_FLAG_STORAGE_SIZE_COMPUTATION"


@pytest.mark.parametrize(
    "feature_flag, upload_size, min_free_space_after_upload_gib, should_raise, match",
    [
        ("true", 30 * 2**30, 5.0, None, None),  # enough space to upload, enough post-upload residual space
        (
            "true",
            30 * 2**30,
            25.0,
            ValueError,
            "Cannot upload media of size 30.00 GiB when only 46.57GB is available: 25.00 GB of space must be kept free",
        ),
        # 2: enough space to upload, but not enough post-upload residual space
        (
            "true",
            70 * 2**30,
            0,
            ValueError,
            "Cannot upload media of size 70.00 GiB when only 46.57GB is available: 0.00 GB of space must be kept free",
        ),
        # 3: not enough space to upload
        ("false", 30 * 2**30, 25.0, None, None),  # same as check 2 with computation disabled (no error raised)
        ("false", 70 * 2**30, 0, None, None),  # same as check 3 with computation disabled (no error raised)
    ],
)
def test_check_free_space_for_upload(
    feature_flag, upload_size, min_free_space_after_upload_gib, should_raise, match
) -> None:
    # Simulate a system 50 GB free disk space, out of a total of 100 GB
    with (
        patch.object(
            BinaryRepo,
            "get_disk_stats",
            return_value=(100_000_000_000, 50_000_000_000, 50_000_000_000),
        ),
        patch.dict(os.environ, {FEATURE_FLAG_STORAGE_SIZE_COMPUTATION: feature_flag}),
    ):
        if should_raise:
            with pytest.raises(should_raise, match=match):
                check_free_space_for_upload(
                    upload_size=upload_size,
                    exception_type=ValueError,
                    min_free_space_after_upload_gib=min_free_space_after_upload_gib,
                )
        else:
            check_free_space_for_upload(
                upload_size=upload_size,
                exception_type=ValueError,
                min_free_space_after_upload_gib=min_free_space_after_upload_gib,
            )


@pytest.mark.parametrize(
    "feature_flag, operation, exception_type, min_free_space, should_raise, match",
    [
        ("true", "Small operation", None, 10.0, False, None),  # enough space to perform operation
        (
            "true",
            "Large operation",
            ValueError,
            100.0,
            True,
            "Cannot perform operation 'Large operation' when there is 46.57GB of storage space left. "
            "At least 100.0GB should be available.",
        ),  # not enough space to perform operation
        ("false", "Large operation", ValueError, 100.0, False, None),  # not enough space but feature flag disabled
    ],
)
def test_check_free_space_for_operation(
    feature_flag, operation, exception_type, min_free_space, should_raise, match
) -> None:
    with (
        patch.object(
            BinaryRepo,
            "get_disk_stats",
            return_value=(100_000_000_000, 50_000_000_000, 50_000_000_000),
        ),
        patch.dict(os.environ, {FEATURE_FLAG_STORAGE_SIZE_COMPUTATION: feature_flag}),
    ):
        if should_raise:
            with pytest.raises(exception_type, match=match):
                check_free_space_for_operation(
                    operation=operation,
                    exception_type=exception_type,
                    min_free_space_for_operation=min_free_space,
                )
        else:
            check_free_space_for_operation(
                operation=operation,
                exception_type=exception_type,
                min_free_space_for_operation=min_free_space,
            )


def test_compute_project_size(fxt_detection_project) -> None:
    with patch.object(BinaryRepo, "get_object_storage_size", return_value=100):
        project_size = compute_project_size(fxt_detection_project)

    # Project contains 5 binary repo's for which size should be computed for, each being 100 bytes.
    assert project_size == 500.0
