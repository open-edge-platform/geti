# Segment Anything example

This example demonstrates how to use a Python API implementation of Segment Anything pipeline inference:

- Create encoder and decoder models
- Create a visual prompter pipeline
- Use points as prompts
- Visualized result is saved to `sam_result.jpg`

## Prerequisites

Install Model API dependencies with examples by running the following command in the root directory of the repository:

```bash
uv sync --extra examples
```

## Run example

To run the example, please execute the following command:

```bash
uv run python run.py <path_to_image> <encoder_path> <decoder_path> <prompts>
```

where prompts are in X Y format.

To run the pipeline out-of-the box you can download the test data by running the following command from the repo root:

```bash
uv run python tests/accuracy/download_models.py -d data -j tests/accuracy/examples.json -l
```

and then run

```bash
uv run python examples/visual_prompting/run.py data/coco128/images/train2017/000000000127.jpg \
     data/otx_models/sam_vit_b_zsl_encoder.xml data/otx_models/sam_vit_b_zsl_decoder.xml \
     274 306 482 295
```

from the sample folder. Here two prompt points are passed via CLI: `(274, 306)` and `(482, 295)`

> _NOTE_: results of segmentation models are saved to `sam_result.jpg` file.
