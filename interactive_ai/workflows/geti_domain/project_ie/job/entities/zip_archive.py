# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines classes to represent exported project archives and their content"""

import abc
import json
import logging
import os
import tempfile
from collections.abc import Generator, Iterable, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from zipfile import ZipFile

from bson import ObjectId, json_util
from iai_core.repos.storage.storage_client import BinaryObjectType

from .exceptions import (
    CollectionAlreadyExistsError,
    CollectionNotFoundError,
    CollectionWriteError,
    InvalidZipFileStructure,
    ManifestAlreadyExistsError,
    ManifestNotFoundError,
    ProjectArchiveParsingError,
    ZipBombDetectedError,
)

logger = logging.getLogger(__name__)


class PublicKeyBytes(bytes):
    """Public key as raw bytes"""


class SignatureBytes(bytes):
    """Digital signature as raw bytes"""


@dataclass(frozen=True)
class Manifest:
    """Manifest of an exported project archive"""

    version: str  # version of the data schema
    export_date: datetime  # date when the project is exported
    min_id: str  # minimum id (ObjectId) found during project export

    @classmethod
    def decode(cls, manifest_data: bytes) -> "Manifest":
        """Decode a Manifest from its JSON bytes representation"""
        # use json_util.object_hook to properly deserialize datetime
        json_manifest = json.loads(manifest_data.decode("utf-8"), object_hook=json_util.object_hook)
        return Manifest(**json_manifest)

    def encode(self) -> bytes:
        """Encode the Manifest to JSON bytes"""
        # use json_util.default to properly serialize datetime
        return json.dumps(asdict(self), default=json_util.default).encode("utf-8")


class ZipArchive(abc.ABC):
    """
    ZipArchive represent a generic zip archive.

    :param zip_file_path: Local file path of the zip archive. If no file exists at the
        specified path, then a new archive will be created.
    :param readonly: If True, open the file in 'read' mode, preventing any modification
        to the content of the archive. If False, the file is opened in 'append' mode.
    """

    def __init__(self, zip_file_path: str, readonly: bool = False) -> None:
        self._zip_file_path = zip_file_path
        self._zip_file = ZipFile(self._zip_file_path, mode="r" if readonly else "a")

    def get_uncompressed_size(self) -> int:
        """Get the overall size of the files in the zip after decompression"""
        return sum(zp.file_size for zp in self._zip_file.infolist())

    def get_compressed_size(self) -> int:
        """Get the overall size of the files in the zip when compressed"""
        return sum(zp.compress_size for zp in self._zip_file.infolist())

    def get_compression_ratio(self) -> float:
        """Get the compression ratio of the zip file."""
        try:
            return self.get_uncompressed_size() / self.get_compressed_size()
        except ZeroDivisionError:
            return 0

    def validate_against_zip_bomb(
        self,
        allow_nested_zip: bool = False,
        max_allowed_compression_ratio: float = 3.0,
    ) -> float:
        """
        Validate that the archive is not a zip bomb.

        Supported checks:
          - limit compression ratio
          - prohibit nested archives

        :param allow_nested_zip: If False, archives that contain .zip files are rejected
        :param max_allowed_compression_ratio: Archives with a compression ratio greater than this value are rejected
        :return: the compression ratio of the archive
        :raises: ZipBombDetectedError if the validation fails
        """
        if not allow_nested_zip:
            for f in self._zip_file.namelist():
                if os.path.splitext(f)[1] == ".zip":
                    logger.warning(
                        "Archive '%s' rejected because it contains a nested zip: %s",
                        self._zip_file_path,
                        f,
                    )
                    raise ZipBombDetectedError

        compression_ratio = self.get_compression_ratio()
        if compression_ratio > max_allowed_compression_ratio:
            logger.warning(
                "Archive '%s' rejected because its compression ratio (%f) is too high (limit %f)",
                self._zip_file_path,
                compression_ratio,
                max_allowed_compression_ratio,
            )
            raise ZipBombDetectedError

        return compression_ratio

    def validate_files_structure(self, files_whitelist: Sequence[str]) -> None:
        """
        Validate the internal files and folders structure of the zip archive.

        :param files_whitelist: Exact list of files that should be present in the archive.
            In case of mismatch, the archive is rejected.
        """
        found_files_set = set(self._zip_file.namelist())
        whitelist_set = set(files_whitelist)
        mismatching_files = found_files_set ^ whitelist_set
        if mismatching_files:
            logger.warning(
                "Archive '%s' rejected because some files are present in the archive "
                "but not in the whitelist, or vice-versa: %s",
                self._zip_file_path,
                mismatching_files,
            )
            raise InvalidZipFileStructure

    def close(self) -> None:
        """
        Close the zip file.

        Calling this method is necessary after adding one or more files to the archive,
        as it writes important metadata at the end of the zip ('Central Directory').
        """
        self._zip_file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: ANN001
        self.close()


class ProjectZipArchive(ZipArchive):
    """
    ProjectZipArchive represents the archive of a project to be imported or exported.
    The class allows reading and writing files in the archive, including the database
    documents, binary objects and the manifest.

    :param zip_file_path: Local file path of the zip archive. If no file exists at the
        specified path, then a new archive will be created.
    :param readonly: If True, open the file in 'read' mode, preventing any modification
        to the content of the archive. If False, the file is opened in 'append' mode.
    """

    MANIFEST_NAME = "manifest.json"
    DOCUMENTS_FOLDER = "documents"
    BINARIES_FOLDER = "binaries"

    def __init__(self, zip_file_path: str, readonly: bool = False) -> None:
        super().__init__(zip_file_path=zip_file_path, readonly=readonly)
        self.__manifest: Manifest | None = None  # created or loaded lazily

    def get_manifest(self) -> Manifest:
        """
        Get the manifest of the project archive

        :return: Manifest object
        :raises ManifestNotFoundError: if the archive does not contain the manifest
        """
        # Fast path: manifest is cached
        if self.__manifest is not None:
            return self.__manifest

        try:
            with self._zip_file.open(self.MANIFEST_NAME) as manifest_fp:
                self.__manifest = Manifest.decode(manifest_fp.read())
                return self.__manifest
        except KeyError:
            raise ManifestNotFoundError

    def add_manifest(self, version: str, min_id: str) -> Manifest:
        """
        Create and add the manifest to the project archive

        :param version: Version of the Geti data schema
        :param min_id: Minimum id (ObjectId) found during export
        :return: Manifest object
        :raises ManifestAlreadyCreatedError: if the archive already contains a manifest
        """
        # If the manifest already exists in the archive, raise an exception
        try:
            self._zip_file.getinfo(self.MANIFEST_NAME)
            raise ManifestAlreadyExistsError
        except KeyError:
            pass

        if not ObjectId.is_valid(min_id):
            raise ValueError("'min_id' must be a valid ObjectId")

        self.__manifest = Manifest(version=version, export_date=datetime.now(timezone.utc), min_id=min_id)
        self._zip_file.writestr(self.MANIFEST_NAME, self.__manifest.encode())
        return self.__manifest

    def get_collection_names(self) -> tuple[str, ...]:
        """
        Get the names of all the collections of documents that are present in the archive

        :return: Tuple of names
        """
        return tuple(
            os.path.basename(filename).removesuffix(".jsonl")
            for filename in self._zip_file.namelist()
            if filename.startswith(self.DOCUMENTS_FOLDER) and filename.endswith(".jsonl")
        )

    def get_object_types(self) -> tuple[BinaryObjectType, ...]:
        """
        Get the names of the types of binary objects that are present in the archive

        :return: Tuple of names
        :raises ProjectArchiveParsingError: if some object type is not recognized
        """
        binary_folder_names = {
            os.path.normpath(filename).split(os.sep)[1]
            for filename in self._zip_file.namelist()
            if filename.startswith(self.BINARIES_FOLDER + os.sep)  # exclude files not rooted in 'binaries'
        }
        try:
            return tuple(BinaryObjectType.from_string(fn) for fn in binary_folder_names)
        except ValueError as ve:
            raise ProjectArchiveParsingError from ve

    def get_documents_by_collection(self, collection_name: str) -> Generator[str, None, None]:
        """
        Get the documents stored in the archive in a specific collection as a stream of BSON encoded strings.

        The collection file should contain one document per line, as in the JSON Lines specification.

        Note that the method is a generator, so exceptions are only raised (lazily) when iterating over the result.

        :param collection_name: Name of the collection
        :return: Generator that yields the documents one by one
        :raises CollectionNotFoundError: If the collection is not present in the archive
        """
        collection_path = os.path.join(self.DOCUMENTS_FOLDER, f"{collection_name}.jsonl")

        try:
            with self._zip_file.open(collection_path) as coll_fp:
                yield from (str(x, "utf-8").strip() for x in coll_fp.readlines())
        except KeyError as ke:
            raise CollectionNotFoundError from ke

    def add_collection_with_documents(self, collection_name: str, documents: Iterable[str]) -> None:
        """
        Create a new collection in the project archive and add documents to it.

        :param collection_name: Name of the collection
        :param documents: Stream of BSON-encoded documents to write to the collection
        """
        collection_path = os.path.join(self.DOCUMENTS_FOLDER, f"{collection_name}.jsonl")

        # If the collection already exists in the archive, raise an exception
        try:
            self._zip_file.getinfo(collection_path)
            raise CollectionAlreadyExistsError
        except KeyError:
            pass

        try:
            with self._zip_file.open(collection_path, mode="w", force_zip64=True) as coll_fp:
                for doc in documents:
                    coll_fp.write(bytes(f"{doc}\n", "utf-8"))
        except Exception as exc:
            raise CollectionWriteError from exc

    def get_objects_by_type(self, object_type: BinaryObjectType) -> Generator[tuple[str, str], None, None]:
        """
        Get the binary objects of a given type from the project archive.

        The function yields a stream of binary files that are extracted from the zip to a local temporary folder.
        The caller must consume each object before requesting the next one, because the corresponding local file is
        automatically deleted on the next iteration.

        :param object_type: Type of the binary objects to extract
        :return: Generator of binary object files as tuple of (local, remote) paths where the local path is the location
            of the binary in the filesystem, and remote is the relative location that the file should have in the
            S3 storage w.r.t. the project root folder.
        """

        zip_objects_folder = os.path.join(self.BINARIES_FOLDER, object_type.name.lower())

        # Create a temporary folder in the local FS to extract the files
        with tempfile.TemporaryDirectory() as local_tmp_folder:
            # Iterate over the zipped binary files of the given type
            for zip_object_path in self._zip_file.namelist():
                if zip_object_path.startswith(zip_objects_folder) and zip_object_path != zip_objects_folder:
                    # Compute the path where to put the file in the local FS and in the remote storage
                    remote_object_path_from_project_root = zip_object_path.removeprefix(zip_objects_folder + os.sep)
                    local_object_path = os.path.join(
                        local_tmp_folder,
                        self.BINARIES_FOLDER,
                        object_type.name.lower(),
                        remote_object_path_from_project_root,
                    )
                    # Extract the file locally
                    self._zip_file.extract(zip_object_path, local_tmp_folder)
                    if not os.path.exists(local_object_path):  # sanity check on local_object_path before returning it
                        logger.error(
                            f"File extracted from the zip cannot be found. "
                            f"zip_object_path={zip_object_path} local_tmp_folder={local_tmp_folder} "
                            f"local_object_path={local_object_path}"
                        )
                        raise RuntimeError("Zip file was not extracted to the expected path")
                    # Yield the local and remote paths
                    yield local_object_path, remote_object_path_from_project_root
                    # Destroy the local file if it still exists (could be removed by the caller)
                    if os.path.exists(local_object_path):
                        os.remove(local_object_path)

    def add_objects_by_type(
        self,
        object_type: BinaryObjectType,
        local_and_remote_paths: Iterable[tuple[str, str]],
    ) -> None:
        """
        Write all binaries for an object type to the project archive

        :param object_type: Type of the binary object
        :param local_and_remote_paths: Tuples of (local, remote) paths where the local
            path is the location of the binary in the filesystem, and remote is the
            relative location in the S3 storage w.r.t. the project root folder.
        """
        zip_objects_folder = os.path.join(self.BINARIES_FOLDER, object_type.name.lower())

        for (
            local_object_path,
            remote_object_path_from_project_root,
        ) in local_and_remote_paths:
            if not os.path.exists(local_object_path):
                logger.error(f"Local object file {local_object_path} not found")
                raise RuntimeError("Object to add to the archive cannot be found locally")
            zip_object_path = os.path.join(zip_objects_folder, remote_object_path_from_project_root)
            self._zip_file.write(local_object_path, zip_object_path)


class ProjectZipArchiveWrapper(ZipArchive):
    """
    ProjectZipArchiveWrapper represents the archive that contains the ProjectZipArchive
    with additional signature and corresponding public key. The structures of the "project.zip" is as follows:
        - "project.zip" -> the actual zip archive containing the exported project data
        - "ecdsa_p384.sig" -> digital signature of "project.zip"
        - "public_key.der" -> public key that can be used to verify the signature
    """

    PROJECT_ARCHIVE = "project.zip"
    ECDSA_P384_SIGNATURE = "ecdsa_p384.sig"
    PUBLIC_KEY = "public_key.der"

    def add_project_archive(self, project_archive_path: str) -> None:
        """Write the nested project archive containing data exported project files"""
        self._zip_file.write(project_archive_path, self.PROJECT_ARCHIVE)

    def extract_project_archive(self) -> str:
        """Extracts and returns the path of the nested project archive containing the exported project files"""
        folder = os.path.dirname(self._zip_file_path)
        self._zip_file.extract(self.PROJECT_ARCHIVE, path=folder)
        return os.path.join(folder, self.PROJECT_ARCHIVE)

    def add_signature(self, signature: SignatureBytes) -> None:
        """
        Write the signature to the project archive

        :param signature: bytes representing a ECDSA P-384 signature
        """
        self._zip_file.writestr(self.ECDSA_P384_SIGNATURE, data=signature)

    def get_signature(self) -> SignatureBytes:
        """Reads the signature from project archive"""
        return SignatureBytes(self._zip_file.read(self.ECDSA_P384_SIGNATURE))

    def add_public_key(self, public_key: PublicKeyBytes) -> None:
        """
        Write the public key to the project archive

        :param public_key: bytes representing the public key with DER encoding
        """
        self._zip_file.writestr(self.PUBLIC_KEY, data=public_key)

    def get_public_key(self) -> PublicKeyBytes:
        """Reads the public key from project archive (DER encoded)"""
        return PublicKeyBytes(self._zip_file.read(self.PUBLIC_KEY))
