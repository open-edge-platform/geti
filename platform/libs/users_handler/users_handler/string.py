"""String manipulation utilities."""

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

import secrets
import string

_CHARSET_LETTERS_DIGITS: str = string.ascii_letters + string.digits


def random_str(length: int) -> str:
    """
    Generates a random string consisting of letters and digits.

    Letters include both lowercase and uppercase characters.
    """
    return "".join(secrets.choice(_CHARSET_LETTERS_DIGITS) for _ in range(length))
