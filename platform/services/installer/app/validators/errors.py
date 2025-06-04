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
A module with errors raised by validator functions.
"""


class ValidationError(ValueError):
    """
    General Validation error raised by validators functions.
    error_messages attribute is used for storing aggregated error messages from multiple
    failed validations.
    If error_messages is not set explicitly, it would be created as list with message attribute as only item.
    """

    def __init__(self, message: str = "", error_messages: list[str] | None = None):
        if error_messages is None:
            error_messages = [message]
        self.error_messages = error_messages
        self.message = message
        super().__init__(self.message)
