# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

Feature: dataset import and export
  The user can export datasets in various formats and import them back into the platform.

  Background: Geti platform with a workspace
    Given a workspace

  Scenario Outline: project creation through dataset import
    Given a '<dataset_format>' dataset with '<annotation_type>'-like annotations
      When the user uploads the dataset to the platform to create a new project
      Then a job of type 'prepare_import_to_new_project' is scheduled
      And the job completes successfully within 3 minutes
      And '<project_type>' is recognized as one of the project types compatible with the dataset
      When the user chooses '<project_type>' as the type of the new project to create via import
      Then a job of type 'perform_import_to_new_project' is scheduled
      And the job completes successfully within 3 minutes
      And a project of type '<project_type>' is created from 'perform_import_to_new_project' job

    @smoke
    Examples:
      | dataset_format | annotation_type       | project_type                |
      | Datumaro       | bounding box          | detection                   |

    Examples:
      | dataset_format | annotation_type       | project_type                |
      | Datumaro       | label                 | multiclass classification   |
      | Datumaro       | multi label           | multilabel classification   |
      | Datumaro       | hierarchical label    | hierarchical classification |
      | Datumaro       | oriented bounding box | oriented detection          |
      | Datumaro       | polygon               | instance segmentation       |
      | Datumaro       | polygon               | semantic segmentation       |
      | Datumaro       | anomaly label         | anomaly detection           |
      | COCO           | bounding box          | detection                   |
      | COCO           | polygon               | instance segmentation       |
      | YOLO           | bounding box          | detection                   |
      | VOC            | label                 | multiclass classification   |
      | VOC            | bounding box          | detection                   |
      | VOC            | polygon               | instance segmentation       |

    @xfail  # Issue: CVS-161846
    Examples:
      | dataset_format | annotation_type       | project_type                |
      | VOC            | multi label           | multilabel classification   |
