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
A module with validating functions for emails.
"""

import re

from click import BadParameter, Context, Parameter

from texts.validators import EmailValidatorsTexts
from validators.errors import ValidationError


def is_email_valid(context: Context, param: Parameter, value: str) -> str:  # noqa: ARG001
    """
    Validates email address format, raises ValidationError if given mail is invalid.

    context: Click context object
    param: Click parameter object
    value: Value of the parameter
    """
    try:
        regex = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
        if not re.fullmatch(regex, str(value)):
            raise ValidationError(EmailValidatorsTexts.invalid_email.format(mail=value))
    except ValidationError as e:
        raise BadParameter(str(e))
    return value
