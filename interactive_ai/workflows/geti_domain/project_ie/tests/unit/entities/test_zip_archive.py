# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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
import json
import os
import tempfile
import zipfile
from datetime import datetime

import pytest
from bson import json_util
from sc_sdk.repos.storage.storage_client import BinaryObjectType

from job.entities import ProjectZipArchive
from job.entities.exceptions import (
    CollectionAlreadyExistsError,
    CollectionNotFoundError,
    ManifestAlreadyExistsError,
    ManifestNotFoundError,
)

DUMMY_VERSION = "1.5"
DUMMY_EXPORT_DATE = datetime(2020, 1, 1)
DUMMY_COLLECTION_NAME_1 = "collection_1"
DUMMY_COLLECTION_NAME_2 = "collection_2"
DUMMY_BINARY_TYPE_1 = BinaryObjectType.IMAGES
DUMMY_BINARY_TYPE_2 = BinaryObjectType.MODELS
DUMMY_BINARY_NAME_1 = f"{DUMMY_BINARY_TYPE_1.name.lower()}/dataset_storages/123/456.bin"
DUMMY_BINARY_NAME_2 = f"{DUMMY_BINARY_TYPE_2.name.lower()}/model_storages/123/456.bin"


@pytest.fixture
def fxt_project_archive_file_path():
    """Fixture that creates a zip archive populated with data"""
    # Create a temporary folder
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_archive_file_path = os.path.join(tmp_dir, "archive.zip")
        with zipfile.ZipFile(project_archive_file_path, "w") as archive_file:
            # Create and add the manifest
            manifest_file_path = os.path.join(tmp_dir, ProjectZipArchive.MANIFEST_NAME)
            manifest_data_json = {
                "version": DUMMY_VERSION,
                "export_date": DUMMY_EXPORT_DATE,
                "min_id": "00000000000000000000000f",
            }
            manifest_data_bytes = json.dumps(manifest_data_json, default=json_util.default).encode("utf-8")
            with open(manifest_file_path, "wb") as manifest_file:
                manifest_file.write(manifest_data_bytes)
            archive_file.write(manifest_file_path, arcname=ProjectZipArchive.MANIFEST_NAME)
            # Create and add documents
            for coll_name in (DUMMY_COLLECTION_NAME_1, DUMMY_COLLECTION_NAME_2):
                coll_file_path = os.path.join(tmp_dir, coll_name)
                docs_bytes = [json.dumps({"key": f"{coll_name}_{i}"}) + "\n" for i in range(3)]
                with open(coll_file_path, "w") as coll_file:
                    coll_file.writelines(docs_bytes)
                doc_zip_path = os.path.join(ProjectZipArchive.DOCUMENTS_FOLDER, coll_name + ".jsonl")
                archive_file.write(coll_file_path, arcname=doc_zip_path)
            # Create and add binaries
            for binary_name in (DUMMY_BINARY_NAME_1, DUMMY_BINARY_NAME_2):
                binary_file_path = os.path.join(tmp_dir, binary_name)
                os.makedirs(os.path.dirname(binary_file_path))
                with open(binary_file_path, "wb") as binary_file:
                    binary_file.write(b"binary_data")
                bin_zip_path = os.path.join(ProjectZipArchive.BINARIES_FOLDER, binary_name)
                archive_file.write(binary_file_path, arcname=bin_zip_path)

        yield project_archive_file_path


@pytest.fixture
def fxt_empty_project_archive_file_path():
    """Fixture to create an empty zip archive"""
    # Create a temporary folder
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_archive_file_path = os.path.join(tmp_dir, "archive.zip")
        yield project_archive_file_path


@pytest.fixture
def fxt_bad_project_archive_file_path():
    """Fixture that creates a zip archive with bad data (no manifest or project data)"""
    # Create a temporary folder
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a dummy file
        dummy_file_path = os.path.join(tmp_dir, "foo.txt")
        with open(dummy_file_path, "wb") as dummy_file:
            dummy_file.write(b"bar")
        # Create a zip archive with the dummy file
        project_archive_file_path = os.path.join(tmp_dir, "archive.zip")
        with zipfile.ZipFile(project_archive_file_path, "w") as archive_file:
            archive_file.write(dummy_file_path, arcname="foo.txt")
        yield project_archive_file_path


@pytest.mark.ProjectIEMsComponent
class TestZipArchive:
    def test_get_uncompressed_size(self, fxt_project_archive_file_path) -> None:
        zip_archive = ProjectZipArchive(zip_file_path=fxt_project_archive_file_path, readonly=True)

        size = zip_archive.get_uncompressed_size()

        assert size > 0

    def test_get_compressed_size(self, fxt_project_archive_file_path) -> None:
        zip_archive = ProjectZipArchive(zip_file_path=fxt_project_archive_file_path, readonly=True)

        size = zip_archive.get_compressed_size()

        assert size > 0

    def test_get_manifest(self, fxt_project_archive_file_path) -> None:
        zip_archive = ProjectZipArchive(zip_file_path=fxt_project_archive_file_path, readonly=True)

        manifest = zip_archive.get_manifest()

        assert manifest.version == DUMMY_VERSION
        assert manifest.export_date == DUMMY_EXPORT_DATE

    def test_get_manifest_bad_archive(self, fxt_bad_project_archive_file_path) -> None:
        zip_archive = ProjectZipArchive(zip_file_path=fxt_bad_project_archive_file_path, readonly=True)

        with pytest.raises(ManifestNotFoundError):
            zip_archive.get_manifest()

    def test_add_manifest(self, fxt_empty_project_archive_file_path, fxt_ote_id) -> None:
        archive_path = fxt_empty_project_archive_file_path
        min_id = fxt_ote_id(123)

        with ProjectZipArchive(zip_file_path=archive_path) as zip_archive:
            zip_archive.add_manifest(version=DUMMY_VERSION, min_id=str(min_id))

        # Read the manifest from a new ProjectZipArchive object to avoid the internal cache
        with ProjectZipArchive(zip_file_path=archive_path, readonly=True) as zip_archive_2:
            found_manifest = zip_archive_2.get_manifest()
        assert found_manifest.version == DUMMY_VERSION
        assert isinstance(found_manifest.export_date, datetime)

        # Creating the manifest twice should fail
        with ProjectZipArchive(zip_file_path=archive_path) as zip_archive, pytest.raises(ManifestAlreadyExistsError):
            zip_archive.add_manifest(version=DUMMY_VERSION, min_id=min_id)

    def test_get_collection_names(self, fxt_project_archive_file_path) -> None:
        with ProjectZipArchive(zip_file_path=fxt_project_archive_file_path, readonly=True) as zip_archive:
            found_names = zip_archive.get_collection_names()

        assert set(found_names) == {DUMMY_COLLECTION_NAME_1, DUMMY_COLLECTION_NAME_2}

    def test_get_object_types(self, fxt_project_archive_file_path) -> None:
        with ProjectZipArchive(zip_file_path=fxt_project_archive_file_path, readonly=True) as zip_archive:
            found_types = zip_archive.get_object_types()

        assert set(found_types) == {DUMMY_BINARY_TYPE_1, DUMMY_BINARY_TYPE_2}

    def test_get_documents_by_collection(self, fxt_project_archive_file_path) -> None:
        with ProjectZipArchive(zip_file_path=fxt_project_archive_file_path, readonly=True) as zip_archive:
            found_docs = list(zip_archive.get_documents_by_collection(collection_name=DUMMY_COLLECTION_NAME_1))

            assert len(found_docs) == 3

            with pytest.raises(CollectionNotFoundError):
                list(zip_archive.get_documents_by_collection(collection_name="non_existing_collection"))

    def test_add_collection_with_documents(self, fxt_project_archive_file_path) -> None:
        new_coll_name = "new_collection"
        new_docs = [json.dumps({"hello": f"world_{i}"}) for i in range(3)]
        with ProjectZipArchive(zip_file_path=fxt_project_archive_file_path) as zip_archive:
            zip_archive.add_collection_with_documents(collection_name=new_coll_name, documents=new_docs)

        with ProjectZipArchive(zip_file_path=fxt_project_archive_file_path) as zip_archive:
            # Check that the collection was correctly created and can be read
            found_docs = list(zip_archive.get_documents_by_collection(collection_name=new_coll_name))
            assert found_docs == new_docs
            # Check that writing the same collection twice throws an error
            with pytest.raises(CollectionAlreadyExistsError):
                zip_archive.add_collection_with_documents(collection_name=new_coll_name, documents=new_docs)

    def test_get_objects_by_type(self, fxt_project_archive_file_path) -> None:
        num_found_objects = 0
        with ProjectZipArchive(zip_file_path=fxt_project_archive_file_path, readonly=True) as zip_archive:
            for obj_local_path, obj_remote_rel_path in zip_archive.get_objects_by_type(BinaryObjectType.IMAGES):
                num_found_objects += 1
                assert os.path.isfile(obj_local_path)
                assert obj_remote_rel_path == DUMMY_BINARY_NAME_1.removeprefix(
                    f"{BinaryObjectType.IMAGES.name.lower()}/"
                )
        assert num_found_objects == 1

    def test_add_objects_by_type(self, fxt_project_archive_file_path) -> None:
        # Arrange: create a few binary objects
        local_and_remote_paths: list[tuple[str, str]] = []
        video_names = ("video1.mp4", "video2.avi")
        with tempfile.TemporaryDirectory() as tmp_dir:
            for video_name in video_names:
                local_video_path = os.path.join(tmp_dir, video_name)
                remote_video_path = os.path.join(f"dataset_storages/123/{video_name}")
                with open(local_video_path, "wb") as video_file:
                    video_file.write(b"video_data")
                local_and_remote_paths.append((local_video_path, remote_video_path))

            # Act: add the objects to the archive
            with ProjectZipArchive(zip_file_path=fxt_project_archive_file_path) as zip_archive:
                zip_archive.add_objects_by_type(
                    object_type=BinaryObjectType.VIDEOS, local_and_remote_paths=local_and_remote_paths
                )

            # Assert: check that the objects have been added to the archive and can be retrieved
            num_found_objs = 0
            remote_paths = [rp for _, rp in local_and_remote_paths]
            with ProjectZipArchive(zip_file_path=fxt_project_archive_file_path, readonly=True) as zip_archive:
                for obj_local_path, obj_remote_rel_path in zip_archive.get_objects_by_type(BinaryObjectType.VIDEOS):
                    num_found_objs += 1
                    assert os.path.basename(obj_local_path) in video_names
                    with open(obj_local_path, "rb") as obj_fp:
                        assert obj_fp.read() == b"video_data"
                    assert obj_remote_rel_path in remote_paths
            assert num_found_objs == len(video_names)
