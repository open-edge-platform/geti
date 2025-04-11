# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

"""
This module implements the repositories for sdk entities
"""

# Load base repos before others to avoid circular imports
from .storage.binary_repo import BinaryRepo  # isort:skip
from .active_model_state_repo import ActiveModelStateRepo
from .annotation_scene_repo import AnnotationSceneRepo
from .annotation_scene_state_repo import AnnotationSceneStateRepo
from .compiled_dataset_shards_repo import CompiledDatasetShardsRepo
from .configurable_parameters_repo import ConfigurableParametersRepo
from .dataset_repo import DatasetRepo
from .dataset_storage_repo import DatasetStorageRepo
from .evaluation_result_repo import EvaluationResultRepo
from .image_repo import ImageRepo
from .label_schema_repo import LabelRepo, LabelSchemaRepo
from .media_score_repo import MediaScoreRepo
from .metadata_repo import MetadataRepo
from .model_repo import ModelRepo
from .model_storage_repo import ModelStorageRepo
from .model_test_result_repo import ModelTestResultRepo
from .project_repo import ProjectRepo
from .suspended_annotation_scenes_repo import SuspendedAnnotationScenesRepo
from .task_node_repo import TaskNodeRepo
from .video_annotation_range_repo import VideoAnnotationRangeRepo
from .video_repo import VideoRepo

__all__ = [
    "ActiveModelStateRepo",
    "AnnotationSceneRepo",
    "AnnotationSceneStateRepo",
    "BinaryRepo",
    "CompiledDatasetShardsRepo",
    "ConfigurableParametersRepo",
    "ConfigurableParametersRepo",
    "DatasetRepo",
    "DatasetStorageRepo",
    "EvaluationResultRepo",
    "ImageRepo",
    "LabelRepo",
    "LabelSchemaRepo",
    "MediaScoreRepo",
    "MetadataRepo",
    "ModelRepo",
    "ModelStorageRepo",
    "ModelTestResultRepo",
    "ProjectRepo",
    "SuspendedAnnotationScenesRepo",
    "TaskNodeRepo",
    "VideoAnnotationRangeRepo",
    "VideoRepo",
]
