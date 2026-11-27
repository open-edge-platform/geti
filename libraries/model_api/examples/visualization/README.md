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
uv run python tests/functional/download_models.py -d data -j tests/functional/examples.json -l
```

and then run

```bash
uv run python examples/visualization/run.py --image data/cards.png --model data/otx_models/ssd-card-detection.xml --output cards_result.jpg
```

## Matching your own label colours

By default the `Visualizer` assigns a colour to each label from a built-in palette. Pass
`label_colors` to render predictions with colours you control, for example the label
colours defined in your project:

```python
from model_api.visualizer import Visualizer

visualizer = Visualizer(label_colors={"car": "#FF0000", "person": (0, 255, 0)})
visualizer.show(image, result)
```

Colours are either any string accepted by PIL (`"#RRGGBB"`, `"red"`, ...) or an
`(R, G, B)` tuple of integers in the 0-255 range. Labels that are not in the mapping keep
their default colour, and invalid colours raise a `ValueError` when the `Visualizer` is
created. The mapping is applied to detection, instance segmentation, classification and
anomaly results.
