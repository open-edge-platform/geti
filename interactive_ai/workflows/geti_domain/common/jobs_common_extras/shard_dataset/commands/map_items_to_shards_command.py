# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging
from dataclasses import dataclass, field

from geti_telemetry_tools import unified_tracing
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.datasets import Dataset
from iai_core.entities.image import Image
from iai_core.entities.video import VideoFrame

from jobs_common.commands.interfaces.command import ICommand
from jobs_common.exceptions import DataShardCreationFailedException

logger = logging.getLogger(__name__)


def _get_sort_keys(item: DatasetItem) -> tuple[str, int]:
    """Create keys for sorting dataset items.

    This is required for the sequential access for VideoFrame as possible while compiling the Arrow shard file.
    """
    if isinstance(item.media, VideoFrame):
        return str(item.media.video.id_), item.media.frame_index
    return item.media.name, 0


@dataclass
class Shard:
    """Shard dataclass

    :param media_size: Total media bytes size of dataset items in the shard
    :param items: Dataset items in the shard
    """

    media_size: int = 0
    items: list[DatasetItem] = field(default_factory=list)

    @property
    def cnt(self) -> int:
        """Number of dataset items in the shard"""
        return len(self.items)

    def append(self, item: DatasetItem) -> None:
        """Append dataset item to the shard"""
        self.items.append(item)
        self.media_size += self._get_media_size(item)

    @staticmethod
    def _get_media_size(item: DatasetItem) -> int:
        """Return media bytes size"""
        if isinstance(item.media, Image):
            return item.media.size
        if isinstance(item.media, VideoFrame):
            # Raw video frame image tensor size
            return item.media.height * item.media.width * 3

        raise TypeError(item.media)


class MapItemsToShardsCommand(ICommand):
    """It divides SC Dataset into a nested list of SC DatasetItems to make dataset shards for each subset.

    :param train_dataset: Dataset for training
    :param max_shard_size: Maximum number of DatasetItems that can be contained in each shard
    :param max_media_size: Maximum bytes of DatasetItems' media that can be contained in each shard
        (Default is 512 MiB)
    """

    def __init__(
        self,
        train_dataset: Dataset,
        max_shard_size: int,
        max_media_size: int = 512 * 1024**2,  # 512 MiB
    ) -> None:
        super().__init__()
        self.train_dataset = train_dataset
        self.max_shard_size = max_shard_size
        self.max_media_size = max_media_size
        self._shards: list[Shard] | None = None

    @unified_tracing
    def execute(self) -> None:
        """
        Create shards for each subset. The shard is a nested list of dataset items.

        :raises DataShardCreationFailedException: if the shards cannot be created
        """
        try:
            items: list[DatasetItem] = list(self.train_dataset)

            items.sort(key=_get_sort_keys)

            self._shards = []

            shard = Shard()
            while items:
                item = items.pop()
                shard.append(item)
                if shard.cnt >= self.max_shard_size or shard.media_size >= self.max_media_size:
                    self._shards.append(shard)
                    shard = Shard()

            if shard.cnt > 0:
                self._shards.append(shard)

        except Exception as exc:
            logger.exception(f"Could not map items to shards for Dataset[id={self.train_dataset.id_}]")
            raise DataShardCreationFailedException from exc

    @property
    def shards(self) -> list[list[DatasetItem]]:
        """Return a nested list of dataset items

        :return: Nested list of dataset items.
        """
        if self._shards is None:
            raise RuntimeError("Please do execute() first")
        return [shards.items for shards in self._shards]
