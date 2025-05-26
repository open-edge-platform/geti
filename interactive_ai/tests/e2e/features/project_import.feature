# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

Feature: project import
  The user can create projects from exported project archives into the platform.

  Background: Geti platform with a workspace
    Given a workspace

  Scenario Outline: project creation through project import
    Given an exported project archive of type '<project_type>'
      When the user uploads the project archive to the platform to create a new project
      Then a job of type 'import_project' is scheduled
      And the job completes successfully within 3 minutes
      And a project of type '<project_type>' is created from 'import_project' job

      @smoke
      Examples:
        | project_type                |
        | detection                   |

      Examples:
        | project_type                |
        | multiclass classification   |
        | multilabel classification   |
        | hierarchical classification |
        | oriented detection          |
        | instance segmentation       |
        | semantic segmentation       |
        | anomaly detection           |
        | detection > segmentation    |
        | detection > classification  |
