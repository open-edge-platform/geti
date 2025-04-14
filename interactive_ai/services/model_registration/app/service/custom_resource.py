"""Module containing base custom resource abstract class and k8s API client classes."""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import abc
import http
import logging
import threading
from collections.abc import AsyncIterator
from typing import Any, Generic, Optional, TypeVar

import dpath.util
import yaml
from kubernetes_asyncio import client, config
from kubernetes_asyncio.client import CoreV1Api, CustomObjectsApi
from kubernetes_asyncio.client.rest import ApiException
from kubernetes_asyncio.config import ConfigException

logger = logging.getLogger(__name__)


class K8SApiClient:
    """
    This class is a thread-wide singleton responsible for initializing default K8s CoreV1 API client.
    If API client has been already initialized in a particular thread, it will be returned by get() class method
    instead of creating a new client.
    """

    thread_local_storage = threading.local()

    @classmethod
    async def get(cls) -> CoreV1Api:
        """Returns API client singleton."""
        if hasattr(cls.thread_local_storage, "core_api"):
            return cls.thread_local_storage.core_api

        try:
            try:
                await config.load_kube_config()
            except (FileNotFoundError, TypeError, ConfigException):
                config.load_incluster_config()

            cls.thread_local_storage.core_api = client.CoreV1Api(client.ApiClient())

            return cls.thread_local_storage.core_api
        except Exception:
            logger.exception(f"Failed to initialize {cls.__name__}")
            raise


class CustomResourceApiClient:
    """Custom Resource API client
    This class is a thread-wide singleton responsible for initializing K8s Custom Resource API client.
    If API client has been already initialized in a particular thread, it will be returned by get() class method
    instead of creating a new client.
    """

    thread_local_storage = threading.local()

    @classmethod
    async def get(cls) -> CustomObjectsApi:
        """Returns custom resource API client."""
        if hasattr(cls.thread_local_storage, "k8s_custom_object_api"):
            return cls.thread_local_storage.k8s_custom_object_api

        try:
            try:
                await config.load_kube_config()
            except (FileNotFoundError, TypeError, ConfigException):
                config.load_incluster_config()

            cls.thread_local_storage.k8s_custom_object_api = client.CustomObjectsApi(client.ApiClient())

            return cls.thread_local_storage.k8s_custom_object_api
        except Exception:
            logger.exception(f"Failed to initialize {cls.__name__}")
            raise


T = TypeVar("T")


class CustomResource(abc.ABC, Generic[T]):
    """
    Abstract Class representing any K8S Custom Resource.
    Methods of this class implements CRUD interface for Custom Resources.
    In the subclass, provide values for api_group_name, crd_plural_name and crd_version class fields.
    """

    api_group_name: str
    crd_plural_name: str
    crd_version: str

    def __init__(
        self, body: dict, name: str | None = None, namespace: str | None = None, auto_remove: bool = False
    ) -> None:
        # self._fields_to_update keeps list of json fields that should be patched when calling self.update()
        # it is assumed that each property setter will properly update this set
        self._fields_to_update: set[str] = set()
        self._body = body
        self.name = name if name else self._body.get("metadata", {}).get("name")
        self.namespace = namespace if namespace else self._body.get("metadata", {}).get("namespace")

        self.labels = {**self.labels, "owned_by_platform": "true"}
        self.auto_remove = auto_remove
        if self.auto_remove:
            self.labels = {**self.labels, "auto_remove": "true"}

    def __repr__(self) -> str:
        def format_field_value(value):  # noqa: ANN001
            return f'"{value}"' if isinstance(value, str) else value

        fields = ", ".join([f"{key}={format_field_value(value)}" for key, value in self.__dict__.items()])
        return f"{self.__class__.__name__}({fields})"

    def __eq__(self, other):  # noqa: ANN001
        if isinstance(self, other.__class__):
            return self.__dict__ == other.__dict__
        return False

    @property
    def body(self) -> dict:
        """Returns custom resource's body."""
        return self._body

    @property
    def metadata(self) -> dict | None:
        """Returns custom resource's metadata."""
        return self._body.get("metadata")

    @metadata.setter
    def metadata(self, value: dict):
        self._body["metadata"] = value
        self._fields_to_update.add("metadata")

    @property
    def creation_timestamp(self) -> str | None:
        """Returns custom resource's creation timestamp."""
        return self._body.get("metadata", {}).get("creationTimestamp")

    @creation_timestamp.setter
    def creation_timestamp(self, value: str):
        if not self._body.get("metadata"):
            self._body["metadata"] = {}
        self._body["metadata"]["creationTimestamp"] = value
        self._fields_to_update.add("metadata.creationTimestamp")

    @property
    def labels(self) -> dict[str, str]:
        """Returns custom resource's labels."""
        return self._body.get("metadata", {}).get("labels", {})

    @labels.setter
    def labels(self, value: dict[str, str]):
        if not self._body.get("metadata"):
            self._body["metadata"] = {}
        self._body["metadata"]["labels"] = value
        self._fields_to_update.add("metadata.labels")

    @property
    def owner_references(self) -> list[dict[str, str]]:
        """Returns custom resource's owner references."""
        return self._body.get("metadata", {}).get("ownerReferences", [])

    @owner_references.setter
    def owner_references(self, value: list[dict[str, str]]):
        if not self._body.get("metadata"):
            self._body["metadata"] = {}
        self._body["metadata"]["ownerReferences"] = value
        self._fields_to_update.add("metadata.ownerReferences")

    @property
    def annotations(self) -> dict[str, str]:
        """Returns custom resource's annotations."""
        return self._body.get("metadata", {}).get("annotations", {})

    @annotations.setter
    def annotations(self, value: dict[str, str]):
        if not self._body.get("metadata"):
            self._body["metadata"] = {}
        self._body["metadata"]["annotations"] = value
        self._fields_to_update.add("metadata.annotations")

    @property
    def spec(self) -> dict | None:
        """Returns custom resource's spec from the body."""
        return self._body.get("spec")

    @spec.setter
    def spec(self, value: dict):
        """Sets the value of spec in the body and schedules it for the update."""
        self._body["spec"] = value
        self._fields_to_update.add("spec")

    @property
    def status(self) -> dict | None:
        """Returns custom resource's status from the body."""
        return self._body.get("status")

    @status.setter
    def status(self, value: dict):
        """Sets the value of status in the body and schedules it for the update."""
        self._body["status"] = value
        self._fields_to_update.add("status")

    @classmethod
    def from_k8s_response_dict(cls, object_dict: dict) -> "CustomResource":
        """Creates custom resource from specified response dict, that is used as a resource body."""
        # Fields below should be opaque to the client, so we simply remove them
        try:
            del object_dict["metadata"]["generation"]
            del object_dict["metadata"]["resourceVersion"]
        except KeyError:
            pass
        return cls(
            name=object_dict["metadata"]["name"],
            body=object_dict,
            namespace=object_dict.get("metadata", {}).get("namespace"),
        )

    @classmethod
    def from_yaml(cls, yaml_template_path: str) -> "CustomResource":
        """Loads specified yaml file and uses it to create custom resource."""
        with open(yaml_template_path, encoding="utf-8") as yaml_template_file:
            resource_body = yaml.safe_load(yaml_template_file)
        return cls(body=resource_body, name=resource_body["metadata"]["name"])

    @classmethod
    async def list(
        cls,
        namespace: str | None = None,
        label_selector: str | None = None,
        **kwargs,  # noqa: ARG003
    ) -> list["CustomResource"]:
        """Lists custom resources"""
        logger.debug(f"Getting list of {cls.__name__} resources.")
        k8s_custom_object_api = await CustomResourceApiClient.get()
        if namespace:
            raw_resources = await k8s_custom_object_api.list_namespaced_custom_object(
                group=cls.api_group_name,
                namespace=namespace,
                plural=cls.crd_plural_name,
                version=cls.crd_version,
                label_selector=label_selector,
            )
        else:
            raw_resources = await k8s_custom_object_api.list_cluster_custom_object(
                group=cls.api_group_name,
                plural=cls.crd_plural_name,
                version=cls.crd_version,
                label_selector=label_selector,
            )

        return [cls.from_k8s_response_dict(raw_resource) for raw_resource in raw_resources["items"]]

    @classmethod
    async def iterate(
        cls,
        limit: int,
        namespace: str,
        label_selector: str | None = None,
        **kwargs,  # noqa: ARG003
    ) -> AsyncIterator["CustomResource"]:
        """
        Return a generator for iterating over list of namespace-scoped Custom Resources.
        Limit parameter defines chunk size of API list_namespaced_custom_object calls.
        """
        logger.debug(f"Getting list of {cls.__name__} resources.")
        k8s_custom_object_api = await CustomResourceApiClient.get()

        _continue = ""

        while True:
            if not _continue:
                raw_resources = await k8s_custom_object_api.list_namespaced_custom_object(
                    group=cls.api_group_name,
                    namespace=namespace,
                    plural=cls.crd_plural_name,
                    version=cls.crd_version,
                    label_selector=label_selector,
                    limit=limit,
                )
            else:
                raw_resources = await k8s_custom_object_api.list_namespaced_custom_object(
                    group=cls.api_group_name,
                    namespace=namespace,
                    plural=cls.crd_plural_name,
                    version=cls.crd_version,
                    label_selector=label_selector,
                    limit=limit,
                    _continue=_continue,
                )
            for raw_resource in raw_resources["items"]:
                yield cls.from_k8s_response_dict(raw_resource)
            _continue = raw_resources["metadata"].get("continue")
            if not _continue:
                break

    @classmethod
    async def get(cls, name: str, namespace: str | None = None) -> Optional["CustomResource"]:
        """Returns defined custom resource with specified name from given namespace."""
        logger.debug(f"Getting {cls.__name__} {name} in namespace {namespace}.")
        k8s_custom_object_api = await CustomResourceApiClient.get()
        try:
            if namespace:
                raw_object = await k8s_custom_object_api.get_namespaced_custom_object(
                    group=cls.api_group_name,
                    namespace=namespace,
                    plural=cls.crd_plural_name,
                    version=cls.crd_version,
                    name=name,
                )
            else:
                raw_object = await k8s_custom_object_api.get_cluster_custom_object(
                    group=cls.api_group_name, plural=cls.crd_plural_name, version=cls.crd_version, name=name
                )

        except ApiException as api_err:
            if api_err.status == http.HTTPStatus.NOT_FOUND:
                logger.debug(f"Failed to find {cls.__name__} {name} in namespace {namespace}.")
                raw_object = None
            else:
                logger.exception(
                    f"The error {api_err.status} has been returned while getting {cls.__name__} "
                    f"{name} object in namespace {namespace}."
                )
                raise

        return cls.from_k8s_response_dict(raw_object) if raw_object else None

    async def create(self, namespace: str | None = None) -> dict:
        """Creates resource in the specified namespace."""
        if not namespace:
            namespace = self.namespace
        logger.debug(f"Creating {self.__class__.__name__} {self.name} in namespace {namespace}.")
        k8s_custom_object_api = await CustomResourceApiClient.get()
        try:
            response = await k8s_custom_object_api.create_namespaced_custom_object(
                group=self.api_group_name,
                namespace=namespace,
                body=self._body,
                plural=self.crd_plural_name,
                version=self.crd_version,
            )
            self.name = response["metadata"]["name"]
            self.namespace = response["metadata"]["namespace"]
            return response
        except (ApiException, KeyError):
            logger.exception(f"Failed to create {self.__class__.__name__} {self.name}.")
            raise

    async def delete(self, propagation_policy: str | None = None) -> object | Any:
        """
        Idempotent deletion method - no exception will be raised if object was already deleted.
        """
        if not self.name:
            raise RuntimeError(f"{self.__class__.__name__} does not have name set.")

        logger.debug(f"Deleting {self.__class__.__name__} {self.name}.")
        k8s_custom_object_api = await CustomResourceApiClient.get()

        delete_body = client.V1DeleteOptions(propagation_policy=propagation_policy)
        try:
            if self.namespace:
                # For some reason delete_namespaced_custom_object does not work as expected -
                # we cannot define name of the resource there, so we use delete_namespaced_custom_object_0
                # instead
                response = await k8s_custom_object_api.delete_namespaced_custom_object(
                    group=self.api_group_name,
                    namespace=self.namespace,
                    plural=self.crd_plural_name,
                    version=self.crd_version,
                    name=self.name,
                    body=delete_body,
                )
            else:
                response = await k8s_custom_object_api.delete_cluster_custom_object(
                    group=self.api_group_name,
                    plural=self.crd_plural_name,
                    version=self.crd_version,
                    name=self.name,
                    body=delete_body,
                )
            return response
        except ApiException as api_err:
            if api_err.status == http.HTTPStatus.NOT_FOUND:
                return api_err.body

            logger.exception(f"Failed to delete {self.__class__.__name__} {self.name}.")
            raise

    async def patch(self) -> dict | None:
        """Patches scheduled fields to update."""
        logger.debug(f"Patching {self.__class__.__name__} {self.name}.")
        k8s_custom_object_api = await CustomResourceApiClient.get()

        patch_body: dict = {}
        if self._fields_to_update:
            for field in self._fields_to_update:
                dpath.util.new(patch_body, field, dpath.util.get(self._body, field, separator="."), separator=".")
            logger.debug(f"Patch body for {self.__class__.__name__} {self.name}: {patch_body}")
        else:
            logger.debug(f"No fields were changed in {self.__class__.__name__} {self.name}, skipping patch.")
            return None
        try:
            if self.namespace:
                response = await k8s_custom_object_api.patch_namespaced_custom_object(
                    group=self.api_group_name,
                    namespace=self.namespace,
                    body=patch_body,
                    plural=self.crd_plural_name,
                    version=self.crd_version,
                    name=self.name,
                    _content_type="application/merge-patch+json",
                )
            else:
                response = await k8s_custom_object_api.patch_cluster_custom_object(
                    group=self.api_group_name,
                    body=patch_body,
                    plural=self.crd_plural_name,
                    version=self.crd_version,
                    name=self.name,
                    _content_type="application/merge-patch+json",
                )
            self._fields_to_update = set()  # Clear after successful update
            return response
        except ApiException:
            logger.exception(f"Failed to patch {self.__class__.__name__} {self.name}.")
            raise
