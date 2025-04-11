# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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
"""This module implements the PersistentEntity base class"""

from geti_types import ID


class PersistentEntity:
    """
    This is a base class for entities that need to be persisted in the database. It
    defines a mandatory `id_` attribute, which is the unique ID by which the object
    will be referenced in the database.
    """

    def __init__(self, id_: ID, ephemeral: bool = True) -> None:
        self._id_ = id_
        self._ephemeral = ephemeral

    @property
    def id_(self) -> ID:
        """
        Returns the unique database ID of the PersistentEntity instance

        :return: ID of the instance
        """
        return self._id_

    @id_.setter
    def id_(self, value: ID) -> None:
        """
        Sets the unique database ID of the PersistentEntity instance

        :param value: ID to set
        """
        self._id_ = value

    def __hash__(self) -> int:
        """
        Returns a hash that uniquely identifies the PersistentEntity instance
        """
        return hash((self.id_, self.__class__.__name__))

    def __repr__(self) -> str:
        """
        Returns the string representation of the PersistentEntity instance
        """
        return f"{self.__class__.__name__}(id_={self.id_})"

    def __eq__(self, other: object) -> bool:
        """
        This method is called when comparing a PersistentEntity instance to an `object`

        :return: True if the object is identical to self, False otherwise
        """
        if not isinstance(other, PersistentEntity):
            return False
        return self.id_ == other.id_

    @property
    def ephemeral(self) -> bool:
        """
        Returns True if the PersistentEntity instance only exists in memory, False if
        it is backed by the database

        :return: True if the instance exists only in memory, False if it is stored in
            the database
        """
        return self._ephemeral

    def mark_as_persisted(self) -> None:
        """
        This method should be called when the PersistentEntity is persisted into the
        database.
        It sets the `ephemeral` property of the entity to `False`
        """
        self._ephemeral = False

    def mark_as_volatile(self) -> None:
        """
        Mark the entity as 'volatile', i.e. not persisted to the database.

        This method must be used cautiously, only in specific situations like:
         - creation of an in-memory clone of a persisted entity, but with a different ID
         - deletion of the entity from the database while keeping the object in-memory
        """
        self._ephemeral = True

    def is_null(self) -> bool:
        """
        Returns True if the instance is a NullEntity, False otherwise

        :return: True if the instance is a NullEntity, False otherwise
        """
        return self.id_ == ID() and not self.ephemeral
