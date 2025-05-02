# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


"""
This module contains Configuration components for the TaskDatasetCounter classes
"""

import attr

from iai_core_py.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core_py.configuration.elements.primitive_parameters import (
    configurable_boolean,
    configurable_integer,
    string_attribute,
)


@attr.s
class DatasetCounterConfig(ConfigurableParameters):
    """
    Class that holds the configurable parameters for the Dataset Counter.
    """

    header = string_attribute("Annotation requirements")
    description = string_attribute("Specify the number of required annotations for a task")

    label_constraint_first_training = configurable_boolean(
        default_value=False,
        header="Label constraint for the first training",
        description="If this is ON, the first training will only be triggered when each label is "
        "present in N images, while N is number of required images for the first "
        "training. Otherwise, first training will be triggered when N images have "
        "been annotated. If first training has been triggered, this parameter will "
        "not take effect.",
        visible_in_ui=True,
    )

    required_images_auto_training = configurable_integer(
        default_value=12,
        min_value=3,
        max_value=10000,
        header="Number of images required for auto-training",
        description="The minimum number of new annotations required "
        "before auto-train is triggered. Auto-training will start every time "
        "that this number of annotations is created.",
        visible_in_ui=True,
    )

    use_dynamic_required_annotations = configurable_boolean(
        default_value=True,
        header="Dynamic required annotations",
        description="Only applicable if auto-training is on. Set this parameter on to let "
        "the system dynamically compute the number of required annotations between training "
        "rounds based on model performance and training dataset size.",
        visible_in_ui=True,
    )

    required_images_auto_training_dynamic = configurable_integer(
        default_value=12,
        min_value=3,
        max_value=10000,
        header="Dynamic minimum number of images required for auto-training",
        description="An optimal minimum number of images required for auto-training, "
        "calculated based on model performance and dataset size",
        visible_in_ui=False,
    )


@attr.s
class AnomalyDatasetCounterConfig(ConfigurableParameters):
    """
    Class that holds the configurable parameters for the Anomaly Dataset Counter.
    """

    header = string_attribute("Annotation requirements")
    description = string_attribute("Specify the number of required annotations for a task")

    required_images_auto_training = configurable_integer(
        default_value=15,
        min_value=6,
        max_value=10000,
        header="Number of required images for auto training",
        description="The minimum number of images that is required before auto-train "
        "is triggered. For the first training round, both normal and "
        "anomalous images are required. For subsequent training rounds, "
        "only normal images are required, but anomalous images can "
        "optionally be added to improve adaptive thresholding performance.",
        visible_in_ui=False,
    )


@attr.s
class ClassificationDatasetCounterConfig(DatasetCounterConfig):
    """
    Class that holds the configurable parameters for the Dataset Counter for
    classification tasks.
    """

    label_constraint_first_training = configurable_boolean(
        default_value=True,
        header="Label constraint for the first training",
        description="If this is ON, the first training will only be triggered when each label is "
        "present in N images, while N is number of required images for the first "
        "training. Otherwise, first training will be triggered when N images have "
        "been annotated. If first training has been triggered, this parameter will "
        "not take effect.",
        visible_in_ui=True,
    )


@attr.s
class KeypointDetectionCounterConfig(DatasetCounterConfig):
    """
    Class that holds the configurable parameters for the Dataset Counter for
    keypoint detection tasks.
    """

    header = string_attribute("Annotation requirements")
    description = string_attribute("Specify the number of required annotations for a task")

    required_images_auto_training = configurable_integer(
        default_value=24,
        min_value=6,
        max_value=10000,
        header="Number of required images for auto training",
        description="The minimum number of new annotations required "
        "before auto-train is triggered. Auto-training will start every time "
        "that this number of annotations is created.",
        visible_in_ui=False,
    )
