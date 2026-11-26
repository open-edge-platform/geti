# Synchronous API example

This example demonstrates how to use a Python API of OpenVINO Model API for synchronous inference as well as basic features such as:

- Instantiate a model
- Preprocessing embedding
- Creating model from local source
- Image Classification and Object Detection

## Prerequisites

Install Model API dependencies with examples by running the following command in the root directory of the repository:

```bash
uv sync --extra examples
```

## Run example

To run the example, please execute the following command in the root directory of the repository:

```bash
uv run python examples/synchronous_api/run.py data/cards.png
```
