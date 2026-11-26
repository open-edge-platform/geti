# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from io import BytesIO
from typing import cast
from zipfile import ZipFile

import numpy as np
import tifffile
from behave import given, then, when
from behave.runner import Context
from requests import Session

from app.api.schemas import ModelView, ProjectView
from app.api.schemas.jobs import JobView
from app.api.schemas.jobs.training import TrainingMetadata
from app.core.jobs.models import JobType
from app.models.model_revision import ModelFormat, ModelPrecision
from tests.bdd.utils.jobs import expect_job_accepted, wait_for_job_completion


@given("an OME image with annotated planes in every training subset is uploaded")  # pyrefly: ignore
def step_upload_annotated_ome(context: Context) -> None:
    """Create a small deterministic OME fixture and annotate planes through the public API."""
    project = cast(ProjectView, context.project)
    session = cast(Session, context.session)
    pixels = np.random.default_rng(42).integers(0, 65536, size=(12, 3, 32, 32), dtype=np.uint16)
    with BytesIO() as payload:
        tifffile.imwrite(payload, pixels, ome=True, metadata={"axes": "ZCYX"}, photometric="minisblack")
        payload.seek(0)
        response = session.post(
            f"{context.base_url}/api/projects/{project.id}/dataset/media",
            files={"file": ("training.ome.tiff", payload, "image/tiff")},
        )
    assert response.status_code == 201, response.text
    media_id = response.json()["id"]
    assert response.json()["type"] == "ome_image", response.text
    for z, subset in enumerate(["training"] * 6 + ["validation"] * 4 + ["testing"] * 2):
        response = session.post(
            f"{context.base_url}/api/projects/{project.id}/dataset/media/{media_id}/annotations",
            params={"z": z, "t": 0},
            json={
                "subset": subset,
                "annotations": [
                    {"labels": [{"id": str(project.task.labels[z % 2].id)}], "shape": {"type": "full_image"}}
                ],
            },
        )
        assert response.status_code == 201, response.text


@when("I quantize the model trained on OME planes")  # pyrefly: ignore
def step_quantize_ome_model(context: Context) -> None:
    """Calibrate against the saved OME training revision rather than virtual plane paths."""
    project = cast(ProjectView, context.project)
    session = cast(Session, context.session)
    training_job = cast(JobView, context.job)
    metadata = training_job.metadata
    assert isinstance(metadata, TrainingMetadata)
    response = session.post(
        f"{context.base_url}/api/jobs",
        json={
            "job_type": JobType.QUANTIZE,
            "project_id": str(project.id),
            "parameters": {
                "model_id": str(metadata.model.id),
                "model_architecture_id": metadata.model.architecture,
                "max_calibration_subset_size": 6,
            },
        },
    )
    job = expect_job_accepted(response)
    context.quantization_job = wait_for_job_completion(session, str(context.base_url), job.job_id)


@then("the quantized OME model can be exported as an OpenVINO archive")  # pyrefly: ignore
def step_export_quantized_ome_model(context: Context) -> None:
    """Download a real INT8 model archive and verify its IR artifacts."""
    project = cast(ProjectView, context.project)
    session = cast(Session, context.session)
    metadata = cast(JobView, context.job).metadata
    assert isinstance(metadata, TrainingMetadata)
    response = session.get(f"{context.base_url}/api/projects/{project.id}/models/{metadata.model.id}")
    assert response.status_code == 200, response.text
    model = ModelView.model_validate(response.json())
    variant = next(
        (v for v in model.variants if v.format == ModelFormat.OPENVINO and v.precision == ModelPrecision.INT8), None
    )
    assert variant is not None, "Quantization did not produce an INT8 OpenVINO variant"
    assert variant.weights_size > 0
    response = session.get(
        f"{context.base_url}/api/projects/{project.id}/models/{model.id}/variants/{variant.id}/binary"
    )
    assert response.status_code == 200, response.text
    with ZipFile(BytesIO(response.content)) as archive:
        for suffix in (".xml", ".bin"):
            assert any(entry.filename.endswith(suffix) and entry.file_size > 0 for entry in archive.infolist())
