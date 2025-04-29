# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines a model related command"""

import abc

from .command import ICommand


class ModelRelatedICommand(ICommand, metaclass=abc.ABCMeta):
    """
    Interface for a command which deals with one or more models.

    It extends :class:`ICommand`.

    Examples are ML commands for training, inference, optimization, ...
    """
