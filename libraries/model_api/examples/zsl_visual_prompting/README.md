# Zero-shot Segment Anything example

This example demonstrates how to use a Python API implementation of Zero-shot Segment Anything pipeline inference:

- Create encoder and decoder models
- Create a zero-shot visual prompter pipeline
- Use points as prompts to learn on one image
- Segment other image using leaned on the previous image representation
- Visualized result is saved to `zsl_sam_result.jpg`

## Prerequisites

Install Model API dependencies with examples by running the following command in the root directory of the repository:

```bash
uv sync --extra examples
```

## Run example

To run the example, please execute the following command:

```bash
uv run python run.py <path_to_source_image> <path_to_target_image> <encoder_path> <decoder_path> <prompts> -t <mask confidence threshold>
```

where prompts are in X Y format. `t` is a threshold to match the reference features from the source image vs features
obtained from the target image.
Higher thresholds leads to lower mask recall in the final prediction, i.e. low confidence masks can be filtered.

To run the pipeline out-of-the box you can download the test data by running the following command from the repo root:

```bash
uv run python tests/accuracy/download_models.py -d data -j tests/accuracy/examples.json -l
```

and then run

```bash
uv run python examples/zsl_visual_prompting/run.py data/coco128/images/train2017/000000000025.jpg \
     data/coco128/images/train2017/000000000072.jpg data/otx_models/sam_vit_b_zsl_encoder.xml \
     data/otx_models/sam_vit_b_zsl_decoder.xml 464 202 -t 0.7

```

from the sample folder. Here one prompt is passed via CLI: `(464 202)`

> _NOTE_: results of segmentation models are saved to `zsl_sam_result.jpg` file.
