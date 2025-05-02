# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module implements name mappers to convert from SC DatasetItem id to Datumaro DatasetItem id"""

from collections import defaultdict

from geti_types import ID
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.video import Video, VideoFrame
from iai_core.repos.base import SessionBasedRepo


class MediaNameIDMapper:
    """
    Return a method getting datumaro image name from sc image name, add suffix if name
    already exists in dm dataset

    :return: method returning unique datumaro name
    """

    def __init__(self) -> None:
        self.name_mappings: defaultdict[str, dict[ID, str]] = defaultdict(dict)
        self.prev_names: set[str] = set()
        self.name_occurrence: dict[str, int] = {}

    def forward(self, item: DatasetItem) -> str:
        sc_id = item.id_
        if isinstance(item.media, VideoFrame):
            name = f"{item.media.name}_frame_{item.media.frame_index}"
        else:
            name = item.media.name

        if name not in self.name_occurrence:
            self.name_occurrence[name] = 0

        if sc_id not in self.name_mappings[name]:
            image_name = name
            while image_name in self.prev_names:
                self.name_occurrence[name] += 1
                image_name = f"{name}__{self.name_occurrence[name]}"

            self.name_mappings[name][sc_id] = image_name
            self.prev_names.add(image_name)

        return self.name_mappings[name][sc_id]


class VideoNameIDMapper:
    """
    Return a method getting datumaro video name from sc video, add suffix if name
    already exists in dm dataset

    :return: method returning unique datumaro name
    """

    def __init__(self) -> None:
        self.name_mappings: defaultdict[str, dict[ID, str]] = defaultdict(dict)
        self.prev_names: set[str] = set()
        self.name_occurrence: dict[str, int] = {}

    def forward(self, item: Video) -> str:
        sc_id = item.id_
        name = item.name

        if name not in self.name_occurrence:
            self.name_occurrence[name] = 0

        if sc_id not in self.name_mappings[name]:
            video_name = name
            while video_name in self.prev_names:
                self.name_occurrence[name] += 1
                video_name = f"{name}__{self.name_occurrence[name]}"

            self.name_mappings[name][sc_id] = video_name
            self.prev_names.add(video_name)

        return self.name_mappings[name][sc_id]


class IDGenerator:
    """Generate a unique ID using DatabaseRepo"""

    def __init__(self, repo_cls: type[SessionBasedRepo]) -> None:
        self.repo_cls = repo_cls

    def __call__(self) -> ID:
        return self.repo_cls.generate_id()


class IDMapper:
    """This class maps an `ID` entity to a string, and vice versa."""

    @staticmethod
    def forward(instance: ID) -> str:
        """Serializes ID to str."""

        return str(instance)
