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

Feature: Obsolete model training
  The user can use obsolete models within restrictions.

  Background: Geti platform with a workspace
  Given a workspace

  Scenario: training, inference and optimization with an obsolete model
    Given a trained project of type 'multiclass classification' trained with 'OTX 1.x'
    And an annotated image of name 'card_nine_spades.jpg'
      Then a model of type 'Custom_Image_Classification_EfficinetNet-B0' exists
      And the model lifecycle stage is obsolete
      When the user tries to optimize a model
      Then the request is rejected
      When the user uploads a single image for prediction
      Then the prediction has label 'Spades'
      When the user requests to train a model
      Then a job of type 'train' is scheduled
      And the job completes successfully within 15 minutes
      And a model of type 'Custom_Image_Classification_EfficinetNet-B0' is created
      And the model lifecycle stage is active
