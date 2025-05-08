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
