# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


Feature: Model Testing
  The user can test and evaluate trained models on different datasets.

  Background: Geti platform with a workspace
    Given a workspace

  Scenario Outline: Model testing with different project types
    Given a trained project of type '<project_type>'
    When the user requests to test the model on the default dataset
    Then a job of type 'test' is scheduled
    And the job completes successfully within 5 minutes
    And a model test report is created
    And the model test report has a non-null score
    And the model test report has a number of media greater than 0

    @smoke
    Examples:
      | project_type |
      | detection    |


    Examples:
      | project_type                |
      | multiclass classification   |
      | multilabel classification   |
      | hierarchical classification |
      | detection                   |
      | oriented detection          |
      | instance segmentation       |
      | semantic segmentation       |
      | anomaly detection           |
