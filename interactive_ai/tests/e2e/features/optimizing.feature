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

Feature: Model optimization
  The user can optimize AI models for any project.

  Background: Geti platform with a workspace
  Given a workspace

  Scenario Outline: POT optimization with default model architecture
    Given a trained project of type '<project_type>'
      And a model of type '<model_template_id>' exists
      When the user requests to optimize a model
      Then a job of type 'optimize_pot' is scheduled
      And the job completes successfully within 10 minutes
      And a model of type '<model_template_id>' and optimization type 'POT' is created

      @smoke
      Examples:
        | project_type                | model_template_id                |
        | detection                   | Custom_Object_Detection_Gen3_SSD |

      Examples:
        | project_type                | model_template_id                                                           |
        | multiclass classification   | Custom_Image_Classification_MobileNet-V3-small                              |
        | oriented detection          | Custom_Rotated_Detection_via_Instance_Segmentation_MaskRCNN_EfficientNetB2B |
        | instance segmentation       | Custom_Instance_Segmentation_RTMDet_tiny                                    |
        | semantic segmentation       | Custom_Semantic_Segmentation_Lite-HRNet-s-mod2_OCR                          |
        | anomaly detection           | ote_anomaly_classification_stfpm                                            |
