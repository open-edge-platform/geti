# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module defines the interface for a data repo in the import/export MS
"""

import abc

from geti_types import ID


class IObjectDataRepo(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def save_file(self, id_: ID, data: bytes):  # noqa: ANN201
        """
        Save data to object storage with specified id

        :param id_: id of the file
        :param data: bytes to write to the file
        """

    @abc.abstractmethod
    def delete_by_id(self, id_: ID) -> None:
        """
        Delete data for a given id

        :param id_: id of data to delete
        """

    @abc.abstractmethod
    def create_multi_upload_file(self, id_: ID) -> str:
        """
        Create a multi-upload file

        :param id_: id of the file
        :return: id of the boto3 upload operation
        """

    @abc.abstractmethod
    def upload_part_to_file(self, id_: ID, upload_id: str, part_number: int, data: bytes) -> str:
        """
        Append data to file with specified id

        :param id_: id of the file
        :param data: bytes to append to the file
        :param upload_id: id of the boto3 upload operation
        :param part_number: part number of the file
        :return: eTag for the part that was added to the file.
        """

    @abc.abstractmethod
    def complete_file_upload(self, id_: ID, upload_id: str, parts: list[dict]) -> None:
        """
        Complete multipart upload of different parts

        :param id_: ID of the file
        :param upload_id: ID of the boto3 upload operation
        :param parts: list of metadata parts
        """

    @abc.abstractmethod
    def abort_multi_part_upload(self, id_: ID, upload_id: str) -> None:
        """
        Abort the multipart upload operation

        :param id_: ID of the file to abort uploading
        :param upload_id: id of the boto3 upload operation
        """
