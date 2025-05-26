# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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

  Scenario: deletion of a project in training
    Given an annotated project of type 'detection'
    And the user requests to train a model
    And a job of type 'train' is running
    And the user waits for 10 seconds
    When the user tries to delete the project
    Then the request is rejected
    When the user cancels the job
    And the user waits for 5 seconds
    And the user deletes the project
    And the user tries to load the project
    Then the request is rejected
