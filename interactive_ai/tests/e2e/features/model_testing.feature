# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


Feature: Model Testing
  The user can test and evaluate trained models on different datasets.

  Background: Geti platform with a workspace
    Given a workspace

  Scenario Outline: Model testing with different project types and datasets
    Given a trained project of type '<project_type>'
    And a '<dataset_format>' dataset with '<annotation_type>'-like annotations
    When the user creates a new dataset with name 'Test'
    Then the project has a dataset with name 'Test'
    When the user uploads a testing set into dataset 'Test'
    Then a job of type 'prepare_import_to_existing_project' is scheduled
    And the job completes successfully within 10 minutes
    When the user requests to test the model on dataset 'Test'
    Then a job of type 'test' is scheduled
    And the job completes successfully within 5 minutes
    And a model test report is created
    And the model test report has a non-null score
    And the model test report has a number of media greater than 0

    @smoke_tester
    Examples:
      | project_type | dataset_format | annotation_type |
      | detection    | Datumaro           | bounding box    |

    Examples:
      | project_type                | dataset_format | annotation_type       |
      | multiclass classification   | Datumaro       | label                 |
      | multilabel classification   | Datumaro       | multi label           |
      | hierarchical classification | Datumaro       | hierarchical label    |
      | detection                   | Datumaro       | bounding box          |
      | oriented detection          | Datumaro       | oriented bounding box |
      | instance segmentation       | Datumaro       | polygon               |
      | semantic segmentation       | Datumaro       | polygon               |
      | anomaly detection           | Datumaro       | anomaly label         |
