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
