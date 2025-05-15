# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from dataclasses import dataclass

from geti_types import ID, PersistentEntity


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
