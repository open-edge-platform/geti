"""Module contains client for K8S api"""

import logging

from kubernetes_asyncio import client, config
from kubernetes_asyncio.client import CoreV1Api
from kubernetes_asyncio.config import ConfigException

logger = logging.getLogger(__name__)


class K8SApiClient:
    """
    This class is responsible for initializing default API client singleton.
    If API client was already initialized, it will be returned by get() class method
    instead of creating a new client.
    """

    def __init__(self, kubeconfig_path: str | None = None) -> None:
        self.core_api: CoreV1Api = None
        self.kubeconfig_path = kubeconfig_path

    @staticmethod
    async def _load_kubeconfig(kubeconfig_path: str | None = None):  # noqa: ANN205
        """Load proper config file"""
        try:
            if kubeconfig_path:
                await config.load_kube_config(config_file=kubeconfig_path)
            else:
                await config.load_kube_config()
        except (FileNotFoundError, TypeError, ConfigException):
            logger.exception(f"Failed to load kubeconfig from {kubeconfig_path}")
            config.load_incluster_config()

    async def _get_core_api(self) -> CoreV1Api:
        """Return k8s core api"""
        if self.core_api:
            return self.core_api
        try:
            self.core_api = client.CoreV1Api(client.ApiClient())
            return self.core_api
        except Exception:
            logger.exception("Failed to initialize K8S CoreV1Api client.")
            raise

    async def __aenter__(self):
        await self._load_kubeconfig(kubeconfig_path=self.kubeconfig_path)
        await self._get_core_api()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):  # noqa: ANN001
        await self.core_api.api_client.close()
        self.core_api = None
