# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


class GetiControllerError(Exception):
    """Custom exception for errors in Geti Controller."""


class GetiControllerCommunicationError(GetiControllerError):
    """Custom exception for errors in Geti Controller communication."""


class GetiControllerInstallationError(GetiControllerError):
    """
    Error raised by function used to deploy Geti Controller chart.
    """


class GetiControllerUninstallationError(GetiControllerError):
    """
    Error raised by function used to remove Geti Controller chart.
    """
