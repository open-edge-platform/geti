# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import patch

import pytest

from sc_sdk.repos import (
    AnnotationSceneRepo,
    AnnotationSceneStateRepo,
    DatasetRepo,
    DatasetStorageRepo,
    ImageRepo,
    MetadataRepo,
    ModelRepo,
    ModelStorageRepo,
    ProjectRepo,
    VideoRepo,
)


def do_nothing(*args, **kwargs):
    pass


@pytest.fixture
def mock_project_repo():
    with patch.object(ProjectRepo, "__init__", new=do_nothing):
        yield


@pytest.fixture
def mock_dataset_storage_repo():
    with patch.object(DatasetStorageRepo, "__init__", new=do_nothing):
        yield


@pytest.fixture
def mock_dataset_repo():
    with patch.object(DatasetRepo, "__init__", new=do_nothing):
        yield


@pytest.fixture
def mock_image_repo():
    with patch.object(ImageRepo, "__init__", new=do_nothing):
        yield


@pytest.fixture
def mock_video_repo():
    with patch.object(VideoRepo, "__init__", new=do_nothing):
        yield


@pytest.fixture
def mock_annotation_scene_repo():
    with patch.object(AnnotationSceneRepo, "__init__", new=do_nothing):
        yield


@pytest.fixture
def mock_annotation_scene_state_repo():
    with patch.object(AnnotationSceneStateRepo, "__init__", new=do_nothing):
        yield


@pytest.fixture
def mock_metadata_repo():
    with patch.object(MetadataRepo, "__init__", new=do_nothing):
        yield


@pytest.fixture
def mock_model_storage_repo():
    with patch.object(ModelStorageRepo, "__init__", new=do_nothing):
        yield


@pytest.fixture
def mock_model_repo():
    with patch.object(ModelRepo, "__init__", new=do_nothing):
        yield
