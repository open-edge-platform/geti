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
import bisect
import itertools
import logging
from collections.abc import Sequence
from dataclasses import dataclass

from cachetools import LRUCache, cachedmethod

from sc_sdk.entities.persistent_entity import PersistentEntity

from geti_types import ID

logger = logging.getLogger(__name__)


class RangeLabelsBucket:
    """
    Class that is used to normalize a list labels
    Difference between RangeLabelsClass:
    RangeLabelsBucket can have an empty sequence of label_ids (RangeLabels can not)
    """

    def __init__(self, start_frame: int, end_frame: int, label_ids: set[ID]) -> None:
        if start_frame > end_frame:
            raise ValueError("Invalid RangeLabels object: start_frame must be <= end_frame")

        self.start_frame = start_frame
        self.end_frame = end_frame
        self.label_ids = label_ids


@dataclass
class RangeLabels:
    """
    Dataclass to hold a list of labels for a range of a video annotation.
    start_frame and end_frame are inclusive.
    """

    start_frame: int
    end_frame: int
    label_ids: Sequence[ID]

    def __post_init__(self):
        self.label_ids = tuple(self.label_ids)

        if self.start_frame > self.end_frame:
            raise ValueError("Invalid RangeLabels object: start_frame must be <= end_frame")

        if self.start_frame < 0 or self.end_frame < 0:
            raise ValueError("Invalid RangeLabels object: start_frame and end_frame must be positive")
        if len(self.label_ids) == 0:
            raise ValueError("Invalid RangeLabels object: at least one label_id must be provided")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RangeLabels):
            return False
        return (
            self.start_frame == other.start_frame
            and self.end_frame == other.end_frame
            and set(self.label_ids) == set(other.label_ids)
        )


class VideoAnnotationRange(PersistentEntity):
    """
    This class represents a video annotation range which holds a dictionary with keys
    for each of the label ids that exist in the video. The dictionaries values are a
    list of frame ranges for each label which are represented in a normalized manner.
    """

    bias = 0.5

    def __init__(
        self,
        video_id: ID,
        range_labels: Sequence[RangeLabels],
        id_: ID,
        ephemeral: bool = True,
    ) -> None:
        """
        Initializes a VideoAnnotationRange object.

        :param video_id: The ID of the video this range is associated with.
        :param range_labels: A list of RangeLabels objects.
        :param id_: The ID of the video annotation range.
        :param ephemeral: True if the VideoAnnotationRange instance exists only in
            memory, False if it is backed up by the database
        """
        super().__init__(id_=id_, ephemeral=ephemeral)
        self.video_id = video_id
        self._range_labels = list(range_labels)
        if not self._is_normalized():
            self._normalize_range_labels()
        # small cache to map frame indices to the respective labels
        self._label_cache = LRUCache(maxsize=16)  # type: ignore

    def __repr__(self) -> str:
        return f"VideoAnnotationRange(id={self.id_}, video_id={self.video_id}, range_labels={self.range_labels})"

    @property
    def range_labels(self) -> tuple[RangeLabels, ...]:
        """
        Returns a tuple with RangeLabels objects.
        """
        return tuple(self._range_labels)

    def _is_normalized(self) -> bool:
        """
        Check if the VideoAnnotationRange object is in normalized representation.

        The VideoAnnotationRange is considered normalized if all of the following are true:
          1. each RangeLabels has a start_frame strictly greater than the end_frame of the previous RangeLabels
          2. if two RangeLabels are adjacent, their labels must not be identical (otherwise they could be merged)
        """
        for previous_range_label, current_range_label in itertools.pairwise(self._range_labels):
            if (  # condition 1: non-overlapping boundaries
                current_range_label.start_frame <= previous_range_label.end_frame
                or (  # condition 2: adjacent ranges must have different labels
                    current_range_label.start_frame - 1 == previous_range_label.end_frame
                    and current_range_label.label_ids == previous_range_label.label_ids
                )
            ):
                return False
        return True

    def _normalize_range_labels(self) -> None:
        """
        Normalizes the range labels in such a way that the start and end frame of each
        of the range labels will not overlap with any other. Matching labels for each of
        these ranges will be grouped together

        Steps:
        1. Identify the keypoints and sort them
        Keypoints are a sequence of indices which delimit a set of intervals whose frames have the same labels
        2. For each interval delimited by two consecutive keypoints initialize an empty bucket of labels
        3. For each input range labels, insert its labels into the corresponding buckets.
        4. Merge consecutive buckets that have the same exact labels
        5. Create new range labels out of the remaining buckets

        In practice, the algorithm implementation sets a bias (+- 0.5) on the intervals endpoints,
        so that the left endpoint is decreased by 0.5 and the right one is increased by 0.5.
        Doing so, one can define a set of non-overlapping consecutive intervals, such that each
        frame is included in the interior of exactly one interval.

        For example, consider this scenario:

        frames [0, 20] -> label A
        frames [5, 10] -> label B
        frames [11, 15] -> label C

        If we subtract the start frames with the bias and add the bias to the end frames we get:
        [-0.5, 20.5]
        [4.5, 10.5]
        [10.5, 15.5]

        That way [4.5, 10.5] and [10.5, 15.5] are connected with each other
        """

        # Step 1
        keypoints = self.__get_all_keypoints()

        # Step 2
        buckets = self.__init_bucket_from_keypoints(keypoints=keypoints)

        # Step 3
        self.__fill_buckets_with_labels(buckets=buckets)

        # Step 4
        merged_buckets = self.__merge_buckets(buckets=buckets)

        # Step 5
        updated_range_labels = self.__convert_buckets_to_range_labels(buckets=merged_buckets)

        self._range_labels = updated_range_labels

    def __get_all_keypoints(self) -> tuple[float, ...]:
        """
        Identifies the key points of the range labels and returns them.
        The bias is applied during this process.

        Example:

        Range Labels:
        frames [0, 20] -> label A
        frames [5, 10] -> label B
        frames [10, 15] -> label C

        Output:
        [-0.5, 4.5, 9.5, 10.5, 15.5, 20.5]

        :return list of unique sorted keypoints
        """
        keypoints = set()
        for range_label in self._range_labels:
            keypoints.add(range_label.start_frame - self.bias)
            keypoints.add(range_label.end_frame + self.bias)
        return tuple(sorted(keypoints))

    def __init_bucket_from_keypoints(self, keypoints: Sequence[float]) -> tuple[RangeLabelsBucket, ...]:
        """
        Converts a list of keypoints to a tuple of RangeLabelsBucket

        :param keypoints: list of unique sorted keypoints

        :return tuple of RangeLabelsBucket
        """
        buckets = []

        for min_interval, max_interval in itertools.pairwise(keypoints):
            bucket = RangeLabelsBucket(
                start_frame=int(min_interval + self.bias),
                end_frame=int(max_interval - self.bias),
                label_ids=set(),
            )

            buckets.append(bucket)
        return tuple(buckets)

    def __fill_buckets_with_labels(self, buckets: Sequence[RangeLabelsBucket]):
        """
        Populates all buckets with appropriate range label ids

        :param buckets: list of RangeLabelsBucket
        """
        for range_label in self._range_labels:
            for bucket in buckets:
                if bucket.start_frame >= range_label.start_frame and bucket.end_frame <= range_label.end_frame:
                    bucket.label_ids |= set(range_label.label_ids)

    def __merge_buckets(self, buckets: Sequence[RangeLabelsBucket]) -> tuple[RangeLabelsBucket, ...]:
        """
        Merges consecutive RangeLabelsBucket's if:
          - the right endpoint of the first bucket matches the left endpoint of the second bucket
          - both buckets have exactly the same labels

          :param buckets: sequence of RangeLabelsBucket

          :return tuple of RangeLabelsBucket
        """
        merged_buckets = list(buckets[:1])

        for bucket in buckets[1:]:
            if (bucket.label_ids == merged_buckets[-1].label_ids) and bucket.start_frame - self.bias <= merged_buckets[
                -1
            ].end_frame + self.bias:
                merged_buckets[-1].end_frame = max(
                    merged_buckets[-1].end_frame,
                    bucket.end_frame,
                )
                merged_buckets[-1].start_frame = min(
                    merged_buckets[-1].start_frame,
                    bucket.start_frame,
                )
            else:
                merged_buckets.append(bucket)
        return tuple(merged_buckets)

    def __convert_buckets_to_range_labels(self, buckets: Sequence[RangeLabelsBucket]) -> list[RangeLabels]:
        """
        Converts each bucket to a RangeLabels object

        :param buckets: sequence of RangeLabelsBucket

        :return list of RangeLabels
        """
        updated_range_labels = []

        for bucket in buckets:
            if len(bucket.label_ids) > 0:
                range_label = RangeLabels(
                    start_frame=bucket.start_frame,
                    end_frame=bucket.end_frame,
                    label_ids=list(bucket.label_ids),
                )
                updated_range_labels.append(range_label)
        return updated_range_labels

    @cachedmethod(lambda self: self._label_cache)  # note: the cache object is bound to the instance to avoid GC issues
    def get_labels_at_frame_index(self, frame_index: int) -> set[ID]:
        """
        Get the labels associated with the frame at the given index.

        :param frame_index: Index of the video frame
        :return: Tuple containing the IDs of the labels at the requested index
        """
        range_index = bisect.bisect_right(self._range_labels, frame_index, key=lambda rl: rl.start_frame)
        if range_index == 0 or frame_index > self._range_labels[range_index - 1].end_frame:
            return set()
        return set(self._range_labels[range_index - 1].label_ids)

    def set_labels_at_frame_index(self, frame_index: int, label_ids: Sequence[ID]) -> None:
        """
        Assign a new set of labels to the frame at the specified index, replacing existing ones (if any).

        Internally, the VideoAnnotationRange object is adjusted to accommodate the new labels
        and ensure that it remains normalized even after the change.

        :param frame_index: Index of the frame where to set the new labels
        :param label_ids: IDs of the labels to assign to the frame.
            The list can be empty, meaning that the frame becomes unannotated.
        """
        # Fast path: the frame already has the same exact labels
        if self.get_labels_at_frame_index(frame_index=frame_index) == set(label_ids):
            return

        # Invalidate cache record
        self._label_cache.pop((frame_index,), None)

        # Check if there is a range label that covers the given frame index
        range_label_to_split_index: int | None = None
        for i, range_label in enumerate(self._range_labels):
            if range_label.start_frame <= frame_index <= range_label.end_frame:
                range_label_to_split_index, range_label_to_split = i, range_label

        if range_label_to_split_index is None:  # case 1: the new labels are assigned to an unannotated frame
            if len(label_ids) > 0:  # case 1.1: there are labels to assign
                new_range_label = RangeLabels(start_frame=frame_index, end_frame=frame_index, label_ids=label_ids)
                logger.debug(f"Inserting {new_range_label} into {self}")
                self._range_labels.append(new_range_label)
                self._normalize_range_labels()
            else:  # case 1.2: no labels to assign, the frame stays unannotated
                logger.debug(f"No RangeLabels to insert at frame {frame_index}")
        else:  # case 2: the new labels are assigned to an annotated frame
            # Extract the pre-existing range label that covers the given frame
            range_label_to_split = self._range_labels.pop(range_label_to_split_index)
            # Split the pre-existing range label in 3 parts in correspondence around the given frame,
            # adjust the labels and re-insert them
            new_range_labels: list[RangeLabels] = []
            if len(label_ids) > 0:
                new_range_labels.append(
                    RangeLabels(start_frame=frame_index, end_frame=frame_index, label_ids=label_ids)
                )
            if frame_index > range_label_to_split.start_frame:  # left chunk of the old range label
                new_range_labels.append(
                    RangeLabels(
                        start_frame=range_label_to_split.start_frame,
                        end_frame=frame_index - 1,
                        label_ids=range_label_to_split.label_ids,
                    )
                )
            if range_label_to_split.end_frame > frame_index:  # right chunk of the old range label
                new_range_labels.append(
                    RangeLabels(
                        start_frame=frame_index + 1,
                        end_frame=range_label_to_split.end_frame,
                        label_ids=range_label_to_split.label_ids,
                    )
                )
            logger.debug(f"Inserting {new_range_labels} into {self}")
            self._range_labels.extend(new_range_labels)
            self._normalize_range_labels()
        logger.debug(f"New state after setting labels {label_ids} at frame {frame_index}: {self}")


class NullVideoAnnotationRange(VideoAnnotationRange):
    """Representation of a 'VideoAnnotationRange' not found'"""

    def __init__(self) -> None:
        super().__init__(video_id=ID(), range_labels=[], id_=ID(), ephemeral=False)
