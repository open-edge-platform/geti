# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
