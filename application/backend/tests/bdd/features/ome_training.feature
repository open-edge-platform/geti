# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
@ome
Feature: Training on annotated OME planes
  As a user working with microscopy images
  I want training revisions to contain rendered annotated planes
  So that training, quantization and model export use persistent image samples

  Scenario: Train, quantize and export a model from annotated OME planes
    Given A classification project "OME training" with labels ['background', 'cell'] exists
    And an OME image with annotated planes in every training subset is uploaded
    And the training configuration for model architecture "resnet18.a1_in1k" is set to 1 epochs
    When I train timm model architecture "resnet18.a1_in1k" on device "cpu"
    Then the trained model has a "openvino" variant with a positive weights size
    When I quantize the model trained on OME planes
    Then the quantized OME model can be exported as an OpenVINO archive
