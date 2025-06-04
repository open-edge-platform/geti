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
A module with validating functions for passwords.
"""

from click import BadParameter, Context, Parameter

from cli_utils.credentials import generate_password
from texts.validators import PasswordValidatorsTexts
from validators.errors import ValidationError

ALLOWED_SPECIAL_CHARACTERS = "!$&()*+,-.:;<=>?@[]^_{|}~"


def is_password_valid(context: Context, param: Parameter, value: str) -> str:
    """
    Check if given password is correct, raise ValidationError otherwise.
    It will create password if it is not provided.

    context: Click context object
    param: Click parameter object
    value: Value of the parameter
    """
    try:
        if not value:
            value = is_password_valid(context=context, param=param, value=generate_password())
        elif not all(
            [
                len(value) >= 8,
                len(value) <= 200,
                any(letter.isupper() for letter in value),
                any(letter.islower() for letter in value),
                any(letter in ALLOWED_SPECIAL_CHARACTERS or letter.isdigit() for letter in value),
            ]
        ):
            raise ValidationError(PasswordValidatorsTexts.invalid_password)
    except ValidationError as e:
        raise BadParameter(str(e))
    return value
