# Visual Prompting

## Description

Visual prompting and zero-shot visual prompting segment objects in images using weak supervision such as point prompts.
Standard visual prompting generates masks from prompts within the same image.
Zero-shot visual prompting captures prompt-supervised features on one image and then segments other images with those features without additional prompts.

## Models

The visual prompting pipeline uses two models: an encoder and a decoder.
The encoder consumes an image and produces features.
The decoder consumes prepared prompt inputs and outputs segmentation masks plus auxiliary results.

### Encoder parameters

The following parameters can be provided via Python API or RT Info embedded into an OpenVINO model:

- `image_size` (`int`): Encoder native input resolution. The input is expected to have a 1:1 aspect ratio.

### Decoder parameters

The following parameters can be provided via Python API or RT Info embedded into an OpenVINO model:

- `image_size` (`int`): Encoder native input resolution. The input is expected to have a 1:1 aspect ratio.
- `mask_threshold` (`float`): Threshold for generating hard predictions from output soft masks.
- `embed_dim` (`int`): Size of the output embedding. This should match the real output size.

## OpenVINO Model Specifications

### Encoder inputs

A single `NCHW` tensor representing a batch of images.

### Encoder outputs

A single `NDHW` tensor, where `D` is the embedding dimension and `HW` is the output feature spatial resolution.

### Decoder inputs

Decoder OpenVINO model should have the following named inputs:

- `image_embeddings` (`B, D, H, W`): Embeddings obtained with encoder.
- `point_coords` (`B, N, 2`): 2D input prompts in XY format.
- `point_labels` (`B, N`): Integer labels of input point prompts.
- `mask_input` (`B, 1, H, W`): Mask for input embeddings.
- `has_mask_input` (`B, 1`): 0/1 flag enabling or disabling applying `mask_input`.
- `ori_shape` (`B, 2`): Resolution of the original image used as input to the encoder wrapper.

### Decoder outputs

- `upscaled_masks` (`B, N, H, W`): Masks upscaled to `ori_shape`.
- `iou_predictions` (`B, N`): IoU predictions for the output masks.
- `low_res_masks` (`B, N, H, W`): Masks in feature resolution.

## Examples

See demos: [VPT](https://github.com/open-edge-platform/model_api/tree/master/model_api/examples/visual_prompting)
and [ZSL-VPT](https://github.com/open-edge-platform/model_api/tree/master/model_api/examples/zsl_visual_prompting).

```{eval-rst}
.. automodule:: model_api.models.visual_prompting
   :members:
   :undoc-members:
   :show-inheritance:
```
