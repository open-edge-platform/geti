# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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
from dataclasses import dataclass

from geti_types import ID
from sc_sdk.entities.persistent_entity import PersistentEntity


@dataclass
class UISettings(PersistentEntity):
    """
    This class can store the UI settings per project per user. This is used solely by
    the UI to configure stuff like annotator tool settings or have settings specific for
    the task type.
    """

    user_id: str
    settings: str
    id_: ID
    project_id: ID | None = None


class NullUISettings(UISettings):
    """Representation of a 'UISettings' not found"""

    def __init__(self) -> None:
        super().__init__(user_id="null user", settings="", id_=ID())
