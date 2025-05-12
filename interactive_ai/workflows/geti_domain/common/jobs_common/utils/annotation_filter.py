# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

from geti_telemetry_tools import unified_tracing
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.datasets import Dataset

logger = logging.getLogger(__name__)


class AnnotationFilter:
    @staticmethod
    @unified_tracing
    def apply_annotation_filters(
        dataset: Dataset,
        max_number_of_annotations: float | None = None,
        min_annotation_size: int | None = None,
    ) -> Dataset:
        """
        WARNING: This replaces the annotations referenced in the dataset. Using this with methods such as
        DatasetRepo.save_deep() can lead to data loss!

        This function applies a filter to filter out small annotations and to limit the maximum amount of annotations in
         an annotations scene.

        :param dataset: Dataset to apply filter to.
        :param min_annotation_size: Minimum size of an annotation in pixels. Any annotation smaller than this will be
        ignored during training
        :param max_number_of_annotations: Maximum number of annotation allowed in one annotation scene. If exceeded, the
        annotation scene will be ignored during training.
        :return: Filtered dataset
        """
        if max_number_of_annotations is None and min_annotation_size is None:
            return dataset
        logger.info(
            f"Applying annotation filter with minimum size: {min_annotation_size} and maximum number of "
            f"annotations: {max_number_of_annotations}"
        )
        max_number_of_annotations = float("inf") if max_number_of_annotations is None else max_number_of_annotations
        for item in list(dataset):
            AnnotationFilter.filter_annotation_size(item, min_annotation_size)
            num_annotations = len(item.annotation_scene.annotations)
            if num_annotations == 0:
                dataset.remove(item)
                logger.info(f"Filtering out item with id '{item.id_}' because it has no annotations")
            elif num_annotations > max_number_of_annotations:
                dataset.remove(item)
                logger.info(
                    f"Filtering out item with id '{item.id_}' because it has too many annotations (found "
                    f"{num_annotations}, max {max_number_of_annotations})"
                )
        return dataset

    @staticmethod
    def filter_annotation_size(item: DatasetItem, min_annotation_size: int | None = None) -> None:
        """
        Filter out annotations from the dataset item that are smaller than the minimum annotation size.
        """
        if min_annotation_size is None:
            return

        annotations = item.annotation_scene.annotations
        for annotation in item.annotation_scene.annotations:
            annotation_size = int(
                annotation.shape.get_area() * item.annotation_scene.media_width * item.annotation_scene.media_height
            )
            if annotation_size < min_annotation_size:
                logger.debug(
                    f"Removing annotation with size: {annotation_size} from annotation scene as it smaller "
                    f"than the minimum annotation size: {min_annotation_size}."
                )
                annotations.remove(annotation)
        item.annotation_scene.annotations = annotations
