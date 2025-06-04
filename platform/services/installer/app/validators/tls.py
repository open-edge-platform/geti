# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.
from click import BadParameter


def check_tls_certificates(tls_cert_file: str | None, tls_key_file: str | None) -> None:
    """
    Check if the provided TLS certificate and key files are valid.
    """
    if bool(tls_cert_file) != bool(tls_key_file):  # XOR logic to check if only one is set
        raise BadParameter("Both --tls-cert-file and --tls-key-file must be set or neither should be set.")
