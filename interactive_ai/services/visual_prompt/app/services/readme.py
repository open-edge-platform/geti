# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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

PROMPT_MODEL_README = """# Visual Prompt Model

## Introduction

This archive contains all the necessary components to run the Visual Prompt Model:

1. **Model Weights**:
   - `encoder.xml` and `encoder.bin`: Encoder architecture and weights.
   - `decoder.xml` and `decoder.bin`: Decoder architecture and weights.

2. **Reference Features**:
   - A JSON file mapping one-shot learned labels to their respective feature vector files.

3. **Feature Vectors**:
   - Feature vectors stored in `.npz` format.

## Usage

To use this model, refer to the example provided in the ModelAPI repository. 
It guides you through installing the required dependencies, loading, and running the Visual Prompt Model.

Check out the example here:  
[ModelAPI Visual Prompting Example](https://github.com/openvinotoolkit/model_api/tree/449ced0ac2841dd61f54e3346dea4fcfe9f34703/examples/python/zsl_visual_prompting)
"""
