# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
