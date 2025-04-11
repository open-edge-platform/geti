#  INTEL CONFIDENTIAL
#
#  Copyright (C) 2023 Intel Corporation
#
#  This software and the related documents are Intel copyrighted materials, and
#  your use of them is governed by the express license under which they were provided to
#  you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
#  publish, distribute, disclose or transmit this software or the related documents
#  without Intel's prior written permission.
#
#  This software and the related documents are provided as is,
#  with no express or implied warranties, other than those that are expressly stated
#  in the License.

from functools import wraps


def return_none(*args, **kwargs) -> None:
    return None


def mock_decorator(*args, **kwargs):
    """Decorate by doing nothing."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)

        return decorated_function

    return decorator
