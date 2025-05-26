# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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