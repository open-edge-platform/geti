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

Feature: media annotation
  The user can annotate media (image/video) files with various types of annotations, depending on the project type.

  Background: Geti platform with a workspace
    Given a workspace


  @smoke
  Scenario: image annotation for multiclass classification
    Given a project of type 'multiclass classification' with labels 'hammer, wrench, screwdriver'
    And an image called 'tool.jpg'
      When the user annotates the image 'tool.jpg' with label 'wrench'
      Then the image 'tool.jpg' has label 'wrench'


  Scenario: image annotation for multilabel classification
    Given a project of type 'multilabel classification' with labels 'tomato, mozzarella, pepperoni, mushrooms, olives'
    And an image called 'pizza.jpg'
      When the user annotates the image 'pizza.jpg' with labels 'tomato, mushrooms'
      Then the image 'pizza.jpg' has labels 'tomato, mushrooms'
      When the user annotates the image 'pizza.jpg' with the empty label
      Then the image 'pizza.jpg' has the empty label

  Scenario: image annotation for hierarchical classification
    Given a project of type 'hierarchical classification' with structure
      """
      Groups: class (mammal, bird, fish); legs (biped, quadruped);
              mammal_reproduction (monotreme, marsupial, placental);
              flight_capability (flying, flightless)
      Hierarchy: mammal->legs; mammal->mammal_reproduction; bird->flight_capability
      """
    And an image called 'animal.jpg'
      When the user annotates the image 'animal.jpg' with labels 'mammal, biped, marsupial'
      Then the image 'animal.jpg' has labels 'mammal, biped, marsupial'
      When the user tries to annotate the image 'animal.jpg' with labels 'bird, marsupial'
      Then the request is rejected

#  Scenario: image annotation for keypoint detection
#    Given a project of type 'keypoint detection' with keypoint structure
#      """
#      Keypoints: head, neck, l_shoulder, r_shoulder, hip &
#      Edges: head-neck, neck-l_shoulder, neck-r_shoulder, neck-hip &
#      Positions: 0.1, 0.2; 0.3, 0.4; 0.5, 0.6; 0.7, 0.8; 0.9, 0.95
#      """
#    And an image called 'animal.jpg'
#      When the user annotates the image 'animal.jpg' with labels 'head, neck, l_shoulder, r_shoulder, hip'
#      Then the image 'animal.jpg' has labels 'head, neck, l_shoulder, r_shoulder, hip'

  @smoke
  Scenario: image annotation for object detection
    Given a project of type 'detection' with labels 'car, truck, motorbike'
    And an image called 'traffic.jpg'
      When the user annotates the image 'traffic.jpg' with labels 'car, motorbike'
      Then the image 'traffic.jpg' has labels 'car, motorbike'
      When the user annotates the image 'traffic.jpg' with the empty label
      Then the image 'traffic.jpg' has the empty label


  Scenario: image annotation for oriented object detection
    Given a project of type 'oriented detection' with labels 'building, parking lot'
    And an image called 'satellite_view.jpg'
      When the user annotates the image 'satellite_view.jpg' with labels 'building, building, parking lot'
      Then the image 'satellite_view.jpg' has labels 'building, building, parking lot'
      When the user annotates the image 'satellite_view.jpg' with the empty label
      Then the image 'satellite_view.jpg' has the empty label


  Scenario: image annotation for semantic segmentation
    Given a project of type 'semantic segmentation' with labels 'sky, road, grass'
    And an image called 'landscape.jpg'
      When the user annotates the image 'landscape.jpg' with labels 'sky, road, grass'
      Then the image 'landscape.jpg' has labels 'sky, road, grass'
      When the user annotates the image 'landscape.jpg' with the empty label
      Then the image 'landscape.jpg' has the empty label


  @smoke
  Scenario: image annotation for instance segmentation
    Given a project of type 'instance segmentation' with labels 'person, bicycle, car'
    And an image called 'city.jpg'
      When the user annotates the image 'city.jpg' with labels 'bicycle, car'
      Then the image 'city.jpg' has labels 'bicycle, car'
      When the user annotates the image 'city.jpg' with the empty label
      Then the image 'city.jpg' has the empty label

  @smoke
  Scenario: image annotation for anomaly detection
    Given a project of type 'anomaly detection'
    And an image called 'product.jpg'
      When the user annotates the image 'product.jpg' with label 'Anomalous'
      Then the image 'product.jpg' has label 'Anomalous'
      When the user annotates the image 'product.jpg' with label 'Normal'
      Then the image 'product.jpg' has label 'Normal'

  @smoke
  Scenario: video annotation for object detection
    Given a project of type 'detection' with labels 'car, truck, motorbike'
    And a video called 'traffic.mp4'
      When the user annotates frame 5 of the video 'traffic.mp4' with labels 'car, motorbike'
      And the user annotates frame 11 of the video 'traffic.mp4' with labels 'car'
      And the user annotates frame 12 of the video 'traffic.mp4' with the empty label
      Then frame 5 of the video 'traffic.mp4' has labels 'car, motorbike'
      And frame 11 of the video 'traffic.mp4' has labels 'car'
      And frame 12 of the video 'traffic.mp4' has the empty label

  @smoke
  Scenario Outline: image annotation for task chain projects
    Given a project of type '<task_chain_project_type>' with labels 'vehicle, car, motorbike'
    And an image called 'traffic.jpg'
      When the user annotates the image 'traffic.jpg' with labels 'vehicle, car'
      Then the image 'traffic.jpg' has labels 'vehicle, car'
      When the user annotates the image 'traffic.jpg' with the empty label
      Then the image 'traffic.jpg' has the empty label

  Examples:
    | task_chain_project_type    |
    | detection > classification |
    | detection > segmentation   |
