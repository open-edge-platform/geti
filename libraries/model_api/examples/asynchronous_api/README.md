# Asynchronous API example

This example demonstrates how to use a Python API of OpenVINO Model API for asynchronous inference and its basic steps:

- Instantiate a model
- Define a callback function for results processing
- Run inference
- Fetch and process results

## Prerequisites

Install Model API dependencies with examples by running the following command in the root directory of the repository:

```bash
uv sync --extra examples
```

## Run example

To run the example, please execute the following command:

```bash
uv run python run.py <path_to_model> <path_to_image>
```

### Example with pre-trained model

In the root directory of the repository:

- download sample models and images by running `uv run python tests/accuracy/download_models.py -d data -j tests/accuracy/examples.json -l`
- run the example with the following command: `uv run python examples/asynchronous_api/run.py data/otx_models/ssd-card-detection.xml data/cards.png`
