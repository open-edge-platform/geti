"""
Module contains class for accessing different types of kubernetes API
"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

from kubernetes import client as k8s
from kubernetes import config as k8s_config

from config import USE_KUBECONFIG

logger = logging.getLogger(__name__)


class K8SException(Exception):
    """
    Exception thrown after failed call to k8s
    """

    def __init__(self, message, reason) -> None:  # noqa: ANN001
        super().__init__()
        self.message = message
        self.reason = reason


class K8S:
    """
    Class for getting k8s_api
    """

    _k8s_api = None
    _custom_k8s_api = None
    _ext_k8s_api = None
    _apps_k8s_api = None
    _cord_k8s_api = None
    _async_k8s_api = None
    _async_custom_k8s_api = None

    @classmethod
    def create_k8s_apis(cls):
        """Create k8s api"""
        if USE_KUBECONFIG:
            logger.info("Using kube_config")
            k8s_config.load_kube_config()
        else:
            logger.info("Using incluster_config")
            k8s_config.load_incluster_config()
        k8s_api_client = k8s.ApiClient()
        cls._ext_k8s_api = k8s.ApiextensionsV1Api(k8s_api_client)
        cls._cord_k8s_api = k8s.CoordinationV1Api(k8s_api_client)
        cls._k8s_api = k8s.CoreV1Api(k8s_api_client)
        cls._custom_k8s_api = k8s.CustomObjectsApi(k8s_api_client)
        cls._apps_k8s_api = k8s.AppsV1Api()

    @classmethod
    def get_ext_k8s_api(cls) -> k8s.CoreV1Api:
        """
        :return: k8s api
        """
        if cls._ext_k8s_api is None:
            cls.create_k8s_apis()
        return cls._ext_k8s_api

    @classmethod
    def get_k8s_api(cls) -> k8s.CoreV1Api:
        """
        :return: k8s api
        """
        if cls._k8s_api is None:
            cls.create_k8s_apis()
        return cls._k8s_api

    @classmethod
    def get_custom_k8s_api(cls) -> k8s.CustomObjectsApi:
        """
        :return: custom object k8s api
        """
        if cls._custom_k8s_api is None:
            cls.create_k8s_apis()
        return cls._custom_k8s_api

    @classmethod
    def get_apps_k8s_api(cls) -> k8s.AppsV1Api:
        """
        :return: apps k8s api
        """
        if cls._apps_k8s_api is None:
            cls.create_k8s_apis()
        return cls._apps_k8s_api

    @classmethod
    def get_cord_k8s_api(cls) -> k8s.CoordinationV1Api:
        """
        :return: coordination k8s api
        """
        if cls._cord_k8s_api is None:
            cls.create_k8s_apis()
        return cls._cord_k8s_api
