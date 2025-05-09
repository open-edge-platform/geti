# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
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

import logging
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

from behave import given, then, when
from behave.runner import Context
from file_management import download_file_from_remote_archive

if TYPE_CHECKING:
    from geti_client import PredictionsApi

logger = logging.getLogger(__name__)


def _predict(context: Context, image_path: Path) -> None:
    predictions_api: PredictionsApi = context.predictions_api

    response = predictions_api.get_single_prediction(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
        pipeline_id="active",
        file=open(str(image_path), "rb").read(),  # noqa: SIM115
        use_cache="never",
        # Workaround for an openapi-generator issue where it always select
        # application/json as the content-type regardless of input parameters.
        # The issue is that this endpoint does not support the "file" parameter
        # using the application/json content-type. Therefore, explicitly override it here.
        # See https://github.com/OpenAPITools/openapi-generator/issues/20871
        _content_type="multipart/form-data",
    )
    context.prediction = response


def _resolve_image_to_upload(images_dir: Path, image_name: str) -> Path:
    local_image_path = images_dir / image_name
    if not local_image_path.exists():
        remote_relative_path = Path(f"images/{image_name}")
        try:
            logger.info(f"Downloading image file from remote archive: {remote_relative_path}")
            download_file_from_remote_archive(
                remote_file_path=remote_relative_path,
                local_file_path=local_image_path,
            )
        except Exception as exc:
            raise FileNotFoundError(
                f"Failed to download image archive file from remote archive: {remote_relative_path}"
            ) from exc
    return local_image_path


@given("an annotated image of name '{image_name}'")
def step_given_annotated_image(context: Context, image_name: str) -> None:
    context.image_to_upload_path = _resolve_image_to_upload(images_dir=context.images_dir, image_name=image_name)


@when("the user uploads a single image for prediction")
def step_when_user_uploads_image_for_prediction(context: Context) -> None:
    _predict(context=context, image_path=context.image_to_upload_path)


@then("the prediction has labels '{raw_expected_label_names}'")
def step_then_prediction_has_expected_labels(context: Context, raw_expected_label_names: str) -> None:
    predictions = context.prediction.predictions

    expected_label_names = raw_expected_label_names.split(", ")

    label_info_by_id = {label.id: label for label in context.label_info_by_name.values()}
    found_label_names = [label_info_by_id[label.id].name for prediction in predictions for label in prediction.labels]
    expected_label_names_freq = Counter(expected_label_names)
    found_label_names_freq = Counter(found_label_names)
    assert expected_label_names_freq == found_label_names_freq, (
        f"Expected to find labels with the respective frequency: {expected_label_names_freq}, "
        f"found instead: {found_label_names_freq}"
    )


@then("the prediction has label '{expected_label_name}'")
def step_then_prediction_has_expected_label(context: Context, expected_label_name: str) -> None:
    step_then_prediction_has_expected_labels(context=context, raw_expected_label_names=expected_label_name)
