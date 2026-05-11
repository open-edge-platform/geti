# Visualization Example

This example demonstrates how to use the Visualizer in VisionAPI.

## Prerequisites

Install Model API dependencies with examples by running the following command in the root directory of the repository:

```bash
uv sync --extra examples
```

## Run example

To run the example, please execute the following command:

```bash
uv run python run.py --image <path_to_image> --model <path_to_model>.xml --output <path_to_output_image>
```

To run the pipeline out-of-the box you can download the test data by running the following command from the repo root:

```bash
uv run python tests/accuracy/download_models.py -d data -j tests/accuracy/examples.json -l
```

and then run

```bash
uv run python examples/visualization/run.py --image data/cards.png --model data/otx_models/ssd-card-detection.xml --output cards_result.jpg
```
