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

Feature: project removal
  The user can remove a project
  
  Background: Geti platform with a workspace
    Given a workspace

  Scenario: deletion of a non-empty project
    Given a project of type 'detection'
    And an image called 'cat.jpg'
      When the user deletes the project
      And the user tries to load the project
      Then the request is rejected
      When the user tries to load the image 'cat.jpg'
      Then the request is rejected

  @wip
  Scenario: deletion of a project in training
    Given an annotated project of type 'detection'
    And the user requests to train a model
    And a job of type 'train' is running
    When the user tries to delete the project
    Then the request is rejected
    When the user cancels the job
    And the user deletes the project
    And the user tries to load the project
    Then the request is rejected
