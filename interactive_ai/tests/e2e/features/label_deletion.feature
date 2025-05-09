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

Feature: label removal
  The user can remove labels from a project as long as the project still has a valid label structure after deletion

  Background: Geti platform with a workspace
    Given a workspace

  Scenario: label deletion resulting in valid label structure
    Given a project of type 'detection' with labels 'foo, bar, baz'
      When the user deletes label 'foo'
      Then the project has labels 'bar, baz'


  Scenario: label deletion resulting in invalid label structure
    Given a project of type 'detection' with labels 'foo'
      When the user tries to delete label 'foo'
      Then the request is rejected
      And the project has labels 'foo'
