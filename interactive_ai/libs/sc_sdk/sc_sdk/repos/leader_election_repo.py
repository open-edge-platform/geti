# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Leader election repo"""

import logging
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from cachetools import cached
from cachetools.keys import hashkey
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from .base.mongo_connector import MongoConnector
from geti_types import ID

logger = logging.getLogger(__name__)


class LeaderElectionRepo:
    """
    Leader election repo
    """

    def __init__(self) -> None:
        self._collection_name = "leader_election"
        # Lazy-load the collection so the repo can be instantiated without MongoDB,
        # to simplify testing; note that MongoDB is of course required to use the repo.
        self.__collection: Collection | None = None

    @staticmethod
    @cached(cache={}, key=lambda collection_name: hashkey(collection_name))
    # Note: the cache ensures that this method is only called once (or at least rarely) per collection;
    # even though 'create_indexes' skips already existing indexes, calling it repeatedly would be a waste of time.
    # As an extra optimization, the 'indexes' property is wrapped by a callable so it's evaluated lazily when needed.
    def __build_indexes(collection_name: str) -> None:
        collection = MongoConnector.get_collection(collection_name=collection_name)
        collection.create_index("resource", unique=True)
        collection.create_index("expiration_date", expireAfterSeconds=0)

    @property
    def _mongo_client(self) -> MongoClient:
        return MongoConnector.get_mongo_client()

    @property
    def _collection(self) -> Collection:
        if self.__collection is None:
            self.__collection = MongoConnector.get_collection(collection_name=self._collection_name)
            self.__build_indexes(collection_name=self._collection_name)
        return self.__collection

    @staticmethod
    def generate_id() -> ID:
        """
        Generates a unique ID that can be assigned to an entity

        :return: Generated ID
        """
        return ID(ObjectId())

    def stand_for_election(self, subject: str, resource: str, validity_in_seconds: int) -> bool:
        """
        Check if 'subject' can become the leader of 'resource' for the next 'validity_in_seconds' seconds

        If no document exist for 'resource', create new document with 'subject' as leader and expiration date set
        'validity_in_seconds' seconds in the future. the 'expiration_date' has a TTL index and MongoDB automatically
        removes documents within 60 seconds after the 'expiration_date'.

        If a document exist for 'resource', a unique index on 'resource' ensures the document can only be updated with
        a new expiration date, if the 'subject' is already leader. Else a DuplicateKeyError is raised, the document is
        not updated.

        If the document is created or updated, and the 'subject' successfully became the leader, True is returned, else
        False.

        :param subject: name or identifier of the subject (usually a pod) that wants to become leader
        :param resource: name of resource (usually a metric to be reported) for which the subject wishes to become
                         leader
        :param validity_in_seconds: number of seconds the subject wishes to become leader of the resource
        :return: bool indicating if the subject successfully became leader of the resource (that is, if the document was
                 updated)
        """
        expiration_date = datetime.now(timezone.utc) + timedelta(seconds=validity_in_seconds)
        try:
            self._collection.find_one_and_update(
                filter={"resource": resource, "leader": subject},
                update={"$set": {"expiration_date": expiration_date}},
                upsert=True,
            )
        except DuplicateKeyError:
            return False
        return True
