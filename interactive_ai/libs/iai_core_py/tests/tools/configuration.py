# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from attr import attrs

from iai_core_py.configuration.elements.configurable_enum import ConfigurableEnum
from iai_core_py.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core_py.configuration.elements.parameter_group import ParameterGroup, add_parameter_group
from iai_core_py.configuration.elements.primitive_parameters import (
    configurable_boolean,
    configurable_float,
    configurable_integer,
    float_selectable,
    selectable,
    string_attribute,
)
from iai_core_py.configuration.enums.model_lifecycle import ModelLifecycle
from iai_core_py.configuration.ui_rules.rules import Action, Operator, Rule, UIRules


class SegmentationNetwork(ConfigurableEnum):
    """
    This Enum represents the architecture used for the model
    """

    UNET = "U-Net"
    DEEPLAB = "DeepLab V3"
    FASTSEG = "Fastseg"


class NormalizationMethod(ConfigurableEnum):
    """
    This Enum represents the type of normalization layer used in the network. Currently only used for UNet models.
    """

    INSTANCE_NORM = "InstanceNorm"
    BATCH_NORM = "BatchNorm"


class DeeplabBackbone(ConfigurableEnum):
    """
    This Enum represents the backbone used for a deeplab model. Only used for Deeplab models.
    """

    RESNET_101 = "ResNet 101"
    RESNET_50 = "ResNet 50"


class AutoAugmentStrategy(ConfigurableEnum):
    """
    This Enum represents the auto augment policy used in training the model.
    """

    NONE = "None"
    IMAGENET = "ImageNet"
    CIFAR10 = "cifar10"
    SVHN = "svhn"


class POTQuantizationPreset(ConfigurableEnum):
    """
    This Enum represents the quantization preset for post training optimization
    """

    PERFORMANCE = "Performance"
    MIXED = "Mixed"


@attrs
class TorchSegmentationConfig(ConfigurableParameters):
    header = string_attribute("Configuration for a segmentation model")
    description = header

    @attrs
    class __LearningArchitecture(ParameterGroup):
        header = string_attribute("Learning Architecture")
        description = header

        model_architecture = selectable(
            default_value=SegmentationNetwork.UNET,
            header="Model architecture",
            description="Switch between U-Net, DeepLab V3 or Fastseg network architecture",
            affects_outcome_of=ModelLifecycle.ARCHITECTURE,
        )

    @attrs
    class __Preprocessing(ParameterGroup):
        header = string_attribute("Preprocessing")
        description = header

        auto_image_size = configurable_boolean(
            header="Automatic image size",
            description="Enable this option to automatically determine the image size for the network "
            "based on the size of the images. The automatic image size is never larger than "
            "the settings for Image width and Image height.",
            default_value=False,
            affects_outcome_of=ModelLifecycle.ARCHITECTURE,
        )

        image_width = float_selectable(
            header="Image width",
            default_value=512,
            options=[256, 320, 385, 512, 640, 768, 1024],
            description="Images will be resized to this width before being propagated through the network. "
            "If automatic image size is enabled, the image will be resized up to a maximum of the width "
            "and height settings.",
            warning="Increasing this value may cause the system to use more memory than available, "
            "potentially causing out of memory errors, please update with caution.",
            affects_outcome_of=ModelLifecycle.ARCHITECTURE,
        )

        image_height = float_selectable(
            header="Image height",
            default_value=512,
            options=[256, 320, 384, 512, 640, 768, 1024],
            description="Images will be resized to this height before being propagated through the network. "
            "If automatic image size is enabled, the image will be resized up to a maximum of the width "
            "and height settings.",
            warning="Increasing this value may cause the system to use more memory than available, "
            "potentially causing out of memory errors, please update with caution.",
            affects_outcome_of=ModelLifecycle.ARCHITECTURE,
        )

    @attrs
    class __Postprocessing(ParameterGroup):
        header = string_attribute("Postprocessing")
        description = header

        blur_strength = configurable_integer(
            header="Blur strength",
            description="With a higher value, the segmentation output will be smoother, but less accurate.",
            default_value=5,
            min_value=1,
            max_value=25,
            affects_outcome_of=ModelLifecycle.INFERENCE,
        )

        soft_threshold = configurable_float(
            default_value=0.5,
            header="Soft threshold",
            description="The threshold to apply to the probability output of the model, for each pixel. A higher value "
            "means a stricter segmentation prediction.",
            min_value=0.0,
            max_value=1,
            affects_outcome_of=ModelLifecycle.INFERENCE,
        )

        full_size_predictions = configurable_boolean(
            header="Generate full size predictions",
            description="For larger images or images with many annotations, disabling this setting increases speed of "
            "generating results, at the cost of less smooth predictions.",
            default_value=True,
            affects_outcome_of=ModelLifecycle.INFERENCE,
        )

    @attrs
    class __DataAugmentation(ParameterGroup):
        header = string_attribute("Data Augmentation")
        description = header

        __ui_rules = UIRules(
            rules=[
                Rule(
                    parameter=["data_augmentation", "auto_augment"],
                    value="None",
                    operator=Operator.EQUAL_TO,
                )
            ],
            action=Action.SHOW,
        )

        auto_augment = selectable(
            default_value=AutoAugmentStrategy.NONE,
            header="Auto augment option",
            description="Options for data augmentation policies.",
            affects_outcome_of=ModelLifecycle.TRAINING,
        )

        rotation_range = configurable_integer(
            header="Rotation range of augmented image",
            description="Degrees of rotation that the image will be rotated left and right. "
            "This is only used if automatic augmentations are disabled.",
            default_value=90,
            min_value=0,
            max_value=180,
            ui_rules=__ui_rules,
            affects_outcome_of=ModelLifecycle.TRAINING,
        )

        scaling_range = configurable_float(
            header="Scaling range of augmented image",
            description="Amount of positive and negative scaling. Implemented as (1-amount, 1+amount). "
            "This is only used if automatic augmentations are disabled.",
            default_value=0.2,
            min_value=0.0,
            max_value=0.99,
            ui_rules=__ui_rules,
            affects_outcome_of=ModelLifecycle.TRAINING,
        )

    @attrs
    class __POTParameter(ParameterGroup):
        header = string_attribute("POT Parameters")
        description = header

        stat_subset_size = configurable_integer(
            header="Number of data samples",
            description="Number of data samples used for post-training optimization ",
            default_value=300,
            min_value=1,
            max_value=1000,
        )

        @attrs
        class __UNetPOTParameters(ParameterGroup):
            header = string_attribute("UNet post-training optimization settings")
            description = header

            preset = selectable(
                default_value=POTQuantizationPreset.MIXED,
                header="Preset",
                description="Quantization preset that defines quantization scheme.",
            )

        unet_pot_parameters = add_parameter_group(__UNetPOTParameters)

        @attrs
        class __DeepLabPOTParameters(ParameterGroup):
            header = string_attribute("DeepLab V3 post-training optimization settings")
            description = header

            preset = selectable(
                default_value=POTQuantizationPreset.MIXED,
                header="Preset",
                description="Quantization preset that defines quantization scheme.",
            )

        deeplab_pot_parameters = add_parameter_group(__DeepLabPOTParameters)

    learning_architecture = add_parameter_group(__LearningArchitecture)
    data_augmentation = add_parameter_group(__DataAugmentation)
    preprocessing = add_parameter_group(__Preprocessing)
    postprocessing = add_parameter_group(__Postprocessing)
    pot_parameters = add_parameter_group(__POTParameter)
