# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

"""This module defines a model related command"""

import abc

from .command import ICommand


class ModelRelatedICommand(ICommand, metaclass=abc.ABCMeta):
    """
    Interface for a command which deals with one or more models.

    It extends :class:`ICommand`.

    Examples are ML commands for training, inference, optimization, ...
    """
