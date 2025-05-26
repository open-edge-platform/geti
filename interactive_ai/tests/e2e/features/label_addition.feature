# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

Feature: label addition
  The user can add labels to projects of all types, except for anomaly detection.

  Background: Geti platform with a workspace
    Given a workspace

  Scenario Outline: label addition for non-anomaly project types
    Given a project of type '<project_type>' with labels 'foo, bar'
      When the user adds a new label 'baz'
      Then the project has labels 'foo, bar, baz'

    @smoke
    Examples:
      | project_type              |
      | detection                 |

    Examples:
      | project_type              |
      | multiclass classification |
      | instance segmentation     |


  Scenario: label addition for anomaly detection
    Given a project of type 'anomaly detection'
      When the user tries to add a new label 'baz'
      Then the request is rejected
      And the project has labels 'Normal, Anomalous'
