# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements the import export data repo
"""

import abc
import json
import logging
import os
import shutil
from collections.abc import Callable

import datumaro as dm
from geti_telemetry_tools import unified_tracing
from geti_types import CTX_SESSION_VAR, ID, Session
from iai_core.utils.file_management import safely_unzip

from job.repos.object_storage_repo import ObjectStorageRepo
from job.utils.exceptions import FileNotFoundException
from job.utils.import_utils import ImportUtils

logger = logging.getLogger(__name__)


class IDataRepo(metaclass=abc.ABCMeta):
    """
    Implements the data repo for the dataset IE MS
    """

    zipped_file_name: str = "dataset.zip"
    dataset_dir_name: str = "dataset"
    import_info_name: str = "import_info.json"

    def __init__(self, root_path: str) -> None:
        self.root_path = root_path
        self.object_storage_repo = ObjectStorageRepo()

    def delete_by_id(self, id_: ID) -> None:
        """
        Delete data for a given id

        :param id_: id of data to delete
        """
        path = os.path.join(self.root_path, str(id_))

        # CVS-134356: If other process write some files while removing dataset_dir, rmtree can fail.
        try:
            shutil.rmtree(path)
        except OSError:
            logger.warning(f"Cannot delete {path}.")

    def get_zipped_file_local_path(self, id_: ID) -> str:
        """
        Get path to zipped file with file id

        :param id_: id of the file
        :return: path to zipped file in the file system
        """
        return os.path.join(self.root_path, str(id_), self.zipped_file_name)

    def get_dataset_directory(self, id_: ID) -> str:
        """
        Get directory of dataset unzipped from file with file id

        :param id_: id of the file
        :return: path to dataset directory
        """
        return os.path.join(self.root_path, str(id_), self.dataset_dir_name)


class ImportDataRepo(IDataRepo):
    import_lock_ext: str = "import_lock"

    def __init__(self, root_path: str | None = None) -> None:
        session: Session = CTX_SESSION_VAR.get()
        self.organization_id = session.organization_id
        self.workspace_id = session.workspace_id
        if root_path is None:
            root_path = os.path.expanduser(os.path.join(os.environ.get("STORAGE_DIR_PATH", "/ie_storage"), "imports"))
        super().__init__(root_path)

    def get_import_lock_file_path(self, id_: ID) -> str:
        """
        Get path to import lock file

        :param id_: id of the file
        :return: path to import lock file
        """
        return os.path.join(self.root_path, f"{str(id_)}.{self.import_lock_ext}")

    def save_import_lock(self, id_: ID) -> None:
        """
        Saves a lock file indicating that dataset import is in progress

        :param id_: id of the file
        """
        lock_path = self.get_import_lock_file_path(id_)
        os.makedirs(os.path.dirname(lock_path), exist_ok=True)
        with open(lock_path, "a"):
            pass

    def clean_import_lock(self, id_: ID) -> None:
        """
        Removes an import lock file

        :param id_: id of the file
        """
        os.remove(self.get_import_lock_file_path(id_))

    def has_import_lock(self, id_: ID) -> bool:
        """
        Checks if import lock file exists

        :param id_: id of the file
        """
        return os.path.isfile(self.get_import_lock_file_path(id_))

    def _save_file(self, id_: ID, data: bytes) -> None:
        """
        Save data to file under $STORAGE_DIR_PATH/<id_>

        :param id_: id of the file to save
        :param data: data to save
        """
        path = self.get_zipped_file_local_path(id_)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as file:
            file.write(data)

    def unzip_dataset(self, import_id: ID, progress_callback: Callable[[int, int], None] | None = None) -> None:
        """
        Unzips the dataset associated with the given import ID into a local directory.

        :param import_id: Import ID for the dataset to be unzipped
        :param progress_callback: An optional callback function that takes two integers
                                  (current progress, total) and returns None. It is called
                                  to update the progress of the extraction.
        :raises FileNotFoundException: If the zipped dataset file is not found.
        """
        zipped_file_local_path = self.get_zipped_file_local_path(id_=import_id)
        local_dataset_directory = self.get_dataset_directory(id_=import_id)
        try:
            safely_unzip(
                zip_file_path=zipped_file_local_path,
                extraction_path=local_dataset_directory,
                max_size_bytes=int(os.environ.get("MAX_IMPORTABLE_DATASET_SIZE_GB", 200)) * 2**30,
                max_num_files=int(os.environ.get("MAX_NUM_FILES_ZIPPED_ARCHIVE", 10**7)),
                unzip_buffer_size_bytes=int(os.environ.get("UNZIP_BUFFER_SIZE_BYTES", 512)),
                progress_callback=progress_callback,
            )
        except FileNotFoundError as e:
            logger.exception(str(e))
            raise FileNotFoundException(f"Given dataset ID({str(import_id)}) is not found")

    def get_import_info_path(self, import_id: ID) -> str:
        """
        Get path to import info of dataset

        :param import_id: Import ID
        :return: path to import info
        """
        return os.path.join(self.root_path, str(import_id), self.import_info_name)

    @unified_tracing
    def save_import_info(self, import_id: ID, dataset: dm.Dataset) -> None:
        """
        Save datumaro dataset info to file system under directory for file with id_.

        :param import_id: Import ID for the dataset
        :param dataset: Datumaro dataset to store its info
        :return: path to dataset directory
        """
        logger.info("Staging dataset through datumaro export")
        info_path = self.get_import_info_path(import_id=import_id)
        info = dataset.infos()
        with open(info_path, "w") as file:
            json.dump(info, file)

    @unified_tracing
    def load_and_transform_dataset(self, import_id: ID) -> dm.Dataset:
        """
        Load datumaro dataset and apply transformations to it according to stored info file

        :param import_id: Import ID for the dataset to be loaded and transformed
        :return: Datumaro dataset
        """
        logger.info("Loading and transforming dataset through datumaro import")
        info_path = self.get_import_info_path(import_id=import_id)

        dataset_dir = self.get_dataset_directory(id_=import_id)
        try:
            with open(info_path) as file:
                dm_infos = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundException(f"Given dataset ID({str(import_id)}) is not found")
        dataset_format = dm_infos.pop("detected_format", None)
        if not dataset_format:  # this shouldn't happen.
            logger.warning("Re-running detect format of dataset since format not found in info file")
            dataset_format = ImportUtils.detect_format(path=dataset_dir)
        dm_dataset, _ = ImportUtils.parse_dataset(path=dataset_dir, fmt=dataset_format)
        dm_dataset.transform("masks_to_polygons")  # TODO: move this later, when really needed.
        multi_label_items = dm_infos.pop("multi_anns", None)
        if multi_label_items:
            dm_dataset.transform("remove_annotations", ids=multi_label_items)
        # restore project_info for further operations.
        dm_dataset.transform("project_infos", dst_infos=dm_infos, overwrite=False)
        return dm_dataset

    def check_file_repo_exists(self, id_: ID) -> bool:
        """
        Check the existence of file repo directory

        :param id_: id of the file
        :return: True if the file repo directory exists
        """
        return os.path.isdir(os.path.join(self.root_path, str(id_)))

    def download_zipped_dataset(self, import_id: ID) -> None:
        """
        Download zipped dataset to filesystem if it does not already exist

        :param import_id: Import ID for the zipped dataset to download
        """
        zipped_file_local_path = self.get_zipped_file_local_path(id_=import_id)
        zipped_file_s3_key = f"{self.get_s3_import_directory(import_id=import_id)}/{self.zipped_file_name}"
        logger.info(
            "Downloading zipped dataset from %s to %s",
            zipped_file_s3_key,
            zipped_file_local_path,
        )
        self.object_storage_repo.download_file(target_path=zipped_file_local_path, key=zipped_file_s3_key)

    def delete_import_data(self, import_id: ID) -> None:
        """
        Delete all data related to import with given import_id

        :param import_id: ID of the import
        """
        s3_directory = f"{self.get_s3_import_directory(import_id=import_id)}"
        self.object_storage_repo.delete_directory(key=s3_directory)

    def upload_import_info(self, import_id: ID) -> None:
        """
        Upload the import info of dataset to object storage.

        :param import_id: Import ID for the dataset
        """
        local_info_path = self.get_import_info_path(import_id=import_id)
        s3_info_name = f"{self.get_s3_import_directory(import_id=import_id)}/{self.import_info_name}"
        logger.info("Uploading import info from %s to %s", local_info_path, s3_info_name)
        self.object_storage_repo.upload_file(source_path=local_info_path, key=s3_info_name)

    def download_import_info(self, import_id: ID) -> None:
        """
        Download the import info of dataset to the file system.

        :param import_id: ID of the dataset
        """
        local_info_path = self.get_import_info_path(import_id=import_id)
        s3_info_name = f"{self.get_s3_import_directory(import_id=import_id)}/{self.import_info_name}"
        logger.info("Downloading import info from %s to %s", s3_info_name, local_info_path)
        self.object_storage_repo.download_file(target_path=local_info_path, key=s3_info_name)

    def get_s3_import_directory(self, import_id: ID) -> str:
        """
        Get the directory structure inside S3 where the import-related files for an organization and workspaces
        are stored.

        :param import_id: ID of the import operation
        :return: Directory structure inside S3 where the import-related files are stored
        """
        return os.path.join(
            os.environ.get("OBJECT_STORAGE_BASE_PATH", ""),
            "organizations",
            str(self.organization_id),
            "workspaces",
            str(self.workspace_id),
            "imports",
            import_id,
        )


class ExportDataRepo(IDataRepo):
    def __init__(self, root_path: str | None = None) -> None:
        session: Session = CTX_SESSION_VAR.get()
        self.organization_id = session.organization_id
        self.workspace_id = session.workspace_id
        if root_path is None:
            root_path = os.path.expanduser(os.path.join(os.environ.get("STORAGE_DIR_PATH", "/ie_storage"), "exports"))
        super().__init__(root_path)

    @unified_tracing
    def zip_dataset(self, export_id: ID) -> int:
        """
        Zip dataset directory with given id to zip file

        :param export_id: Export ID for the dataset to zip
        :return: Size of the zipped file
        """
        directory_path = self.get_dataset_directory(id_=export_id)
        shutil.make_archive(directory_path, "zip", directory_path)
        return os.path.getsize(self.get_zipped_file_local_path(id_=export_id))

    def upload_zipped_dataset(self, export_id: ID) -> None:
        """
        Upload zipped dataset to object storage

        :param export_id: Export ID for the dataset to upload
        """
        zipped_file_s3_key = f"{self.get_s3_export_directory(export_id=export_id)}/{self.zipped_file_name}"
        zipped_file_local_path = self.get_zipped_file_local_path(id_=export_id)
        self.object_storage_repo.upload_file(source_path=zipped_file_local_path, key=zipped_file_s3_key)

    def get_s3_export_directory(self, export_id: ID) -> str:
        """
        Get the directory structure inside S3 where the export-related files for an organization and workspaces
        are stored.

        :param export_id: ID of the export operation
        :return: Directory structure inside S3 where the export-related files are stored
        """
        return os.path.join(
            os.environ.get("OBJECT_STORAGE_BASE_PATH", ""),
            "organizations",
            str(self.organization_id),
            "workspaces",
            str(self.workspace_id),
            "exports",
            export_id,
        )
