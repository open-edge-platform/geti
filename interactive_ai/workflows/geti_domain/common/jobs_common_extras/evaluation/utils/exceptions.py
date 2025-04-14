# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from jobs_common.exceptions import TaskErrorMessage


class MissingTilingConfiguration(Exception):
    """
    Exception raised when there are missing parameters in the model's tiling configuration.

    :param parameter: name of the missing tiling parameter
    """

    def __init__(self, parameter: str) -> None:
        message = f"Tiling configuration has missing parameter: '{parameter}'."
        super().__init__(message)


class EmptyEvaluationDatasetException(Exception, TaskErrorMessage):
    """
    Exception raised when the dataset for evaluation is empty.

    :param subset: Dataset subset to evaluate
    :param max_number_of_annotations: Maximum number of annotations configured for the annotation filter
    :param min_annotation_size: Minimum size of annotations configured for the annotation filter
    """

    def __init__(
        self, subset: str, max_number_of_annotations: int | None = None, min_annotation_size: int | None = None
    ) -> None:
        if max_number_of_annotations is not None or min_annotation_size is not None:
            ann_filter_config_warning = (
                f" This could be the result of a too strict annotation filter configuration; "
                f"please review these settings and try again. Current values: "
                f"{{max_number_of_annotations={max_number_of_annotations}, min_annotation_size={min_annotation_size}}}"
            )
        else:
            ann_filter_config_warning = ""

        message = f"Cannot run evaluation because the dataset ('{subset}' subset) is empty.{ann_filter_config_warning}"
        super().__init__(message)
