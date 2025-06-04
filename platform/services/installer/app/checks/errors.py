# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

"""
A module containing exceptions raised by checks functions.
"""


class CheckError(Exception):
    """
    Error raised by check function.
    """


class CheckSkipped(CheckError):
    """
    Check was skipped.
    """


class CheckIgnored(CheckError):
    """
    Check was ignored.
    """


class CheckWarning(CheckError):
    """
    Check failed, but it is not critical.
    """


class K8SCheckError(CheckError):
    """
    Error raised by check functions interacting with K8S.
    """


class K8SCheckWarning(CheckWarning):
    """
    Warning raised by check functions interacting with K8S.
    """


class K3SCheckError(CheckError):
    """
    Error raised by check functions interacting with k3s.
    """


class DNSCheckError(CheckError):
    """
    Error raise by check function of DNS resolves
    """


class CurlInternetCheckError(CheckError):
    """
    Error raised by check functions interacting with the curl.
    """


class SnapCheckError(CheckError):
    """
    Error raised by check functions interacting with the snap package management system.
    """


class LocalOSCheckError(CheckError):
    """
    Error raised by check functions interacting with local OS.
    """


class LocalOSCheckWarning(CheckWarning):
    """
    Warning raised by check functions interacting with local OS.
    """


class PortsAvailabilityCheckError(CheckError):
    """
    Error raised by ports availability check function.
    """


class ResourcesCheckError(CheckError):
    """
    Error raised by local resources check functions.
    """


class ResourcesCheckWarning(CheckWarning):
    """
    Warning raised by local resources check functions.
    """


class UnsupportedGpuError(CheckError):
    """
    Error raised by local GPU check function.
    """


class UnsupportedGpuWarning(CheckWarning):
    """
    Warning raised by local GPU check function.
    """


class LocalUserCheckError(CheckError):
    """
    Error raised by check functions interacting with local user.
    """


class VenvCheckError(CheckError):
    """
    Error raised by check functions interacting with virtual environment.
    """


class VenvContentCheckError(CheckError):
    """
    Error raised by check functions verifying content of virtual environment.
    """


class CumulativeCheckError(Exception):
    """
    Error raised by checks running function, aggregating all the failed checks.
    Attributes:
        exceptions - list of exceptions raised by failed checks.
    """

    def __init__(self, exceptions: list[CheckError]):
        super().__init__()
        self.exceptions = exceptions
