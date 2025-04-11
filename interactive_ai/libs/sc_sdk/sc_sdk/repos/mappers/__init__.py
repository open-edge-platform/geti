#
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
#

from .cursor_iterator import CursorIterator
from .mongodb_mapper_interface import *  # noqa: F403
from .mongodb_mappers.active_model_state_mapper import ActiveModelStateToMongo
from .mongodb_mappers.annotation_mapper import AnnotationSceneToMongo, AnnotationToMongo
from .mongodb_mappers.annotation_scene_state_mapper import AnnotationSceneStateToMongo
from .mongodb_mappers.compiled_dataset_shards_mapper import CompiledDatasetShardsToMongo
from .mongodb_mappers.configurable_parameters_mapper import ConfigurableParametersToMongo
from .mongodb_mappers.dataset_mapper import DatasetItemToMongo, DatasetToMongo
from .mongodb_mappers.dataset_storage_mapper import DatasetStorageToMongo
from .mongodb_mappers.evaluation_result_mapper import EvaluationResultToMongo
from .mongodb_mappers.id_mapper import IDToMongo
from .mongodb_mappers.label_mapper import LabelGroupToMongo, LabelSchemaToMongo, LabelToMongo, ScoredLabelToMongo
from .mongodb_mappers.media_mapper import (
    ImageIdentifierToMongo,
    ImageToMongo,
    MediaIdentifierToMongo,
    VideoIdentifierToMongo,
    VideoToMongo,
)
from .mongodb_mappers.media_score_mapper import MediaScoreToMongo
from .mongodb_mappers.metadata_mapper import FloatMetadataToMongo, MetadataItemToMongo, TensorToMongo
from .mongodb_mappers.metrics_mapper import PerformanceToMongo, VisualizationInfoToMongo
from .mongodb_mappers.model_mapper import ModelToMongo
from .mongodb_mappers.model_storage_mapper import ModelStorageToMongo
from .mongodb_mappers.model_test_result_mapper import ModelTestResultToMongo
from .mongodb_mappers.primitive_mapper import DatetimeToMongo, NumpyToMongo
from .mongodb_mappers.project_mapper import ProjectToMongo
from .mongodb_mappers.suspended_scenes_mapper import SuspendedAnnotationScenesDescriptorToMongo
from .mongodb_mappers.task_node_mapper import TaskNodeToMongo
from .mongodb_mappers.video_annotation_range_mapper import VideoAnnotationRangeToMongo

__all__ = [
    "ActiveModelStateToMongo",
    "AnnotationSceneStateToMongo",
    "AnnotationSceneToMongo",
    "AnnotationToMongo",
    "CompiledDatasetShardsToMongo",
    "ConfigurableParametersToMongo",
    "CursorIterator",
    "DatasetItemToMongo",
    "DatasetStorageToMongo",
    "DatasetToMongo",
    "DatetimeToMongo",
    "EvaluationResultToMongo",
    "FloatMetadataToMongo",
    "IDToMongo",
    "ImageIdentifierToMongo",
    "ImageToMongo",
    "LabelGroupToMongo",
    "LabelSchemaToMongo",
    "LabelToMongo",
    "MediaIdentifierToMongo",
    "MediaScoreToMongo",
    "MetadataItemToMongo",
    "ModelStorageToMongo",
    "ModelTestResultToMongo",
    "ModelToMongo",
    "NumpyToMongo",
    "PerformanceToMongo",
    "ProjectToMongo",
    "ScoredLabelToMongo",
    "SuspendedAnnotationScenesDescriptorToMongo",
    "TaskNodeToMongo",
    "TensorToMongo",
    "VideoAnnotationRangeToMongo",
    "VideoIdentifierToMongo",
    "VideoToMongo",
    "VisualizationInfoToMongo",
]
