# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
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

Feature: Model training
  The user can train AI models for any project.

  Background: Geti platform with a workspace
  Given a workspace

  Scenario Outline: training with default model architecture
    Given an annotated project of type '<project_type>'
      When the user requests to train a model
      Then a job of type 'train' is scheduled
      And the job completes successfully within 15 minutes
      And a model of type '<model_template_id>' is created
      And the model has training-time statistics
      And the model has a training dataset

      @smoke
      Examples:
        | project_type                | model_template_id                           |
        | multiclass classification   | Custom_Image_Classification_EfficinetNet-B0 |

      @xfail  # https://jira.devtools.intel.com/browse/CVS-164635
      Examples:
        | project_type                | model_template_id                           |
        | detection > segmentation    | Custom_Object_Detection_Gen3_ATSS                                           |

      Examples:
        | project_type                | model_template_id                                                           |
        | multilabel classification   | Custom_Image_Classification_EfficinetNet-B0                                 |
        | hierarchical classification | Custom_Image_Classification_EfficinetNet-B0                                 |
        | detection                   | Custom_Object_Detection_Gen3_ATSS                                           |
        | oriented detection          | Custom_Rotated_Detection_via_Instance_Segmentation_MaskRCNN_EfficientNetB2B |
        | instance segmentation       | Custom_Counting_Instance_Segmentation_MaskRCNN_EfficientNetB2B              |
        | semantic segmentation       | Custom_Semantic_Segmentation_Lite-HRNet-18-mod2_OCR                         |
        | anomaly detection           | ote_anomaly_classification_padim                                            |
        | detection > classification  | Custom_Object_Detection_Gen3_ATSS                                           |