# Visual Prompting with Zero-shot Learning

## Use case and high-level description

Visual Prompting and Zero-shot visual prompting allow to segment object on images
using only weak supervision such as point prompts.
Standard Visual Prompting task implies generating masks by given prompts within the same image.
Zero-shot visual prompting allows to capture prompt-supervised features on one image,
and then segment other images using these features without any additional prompts.

## Models

VPT pipeline uses two models: encoder and decoder.
Encoder consumes an image and produces features, while decoder consumes a specially
prepared inputs that includes prompts and outputs segmentation and some auxiliary results.

### Encoder parameters

The following parameters can be provided via python API or RT Info embedded into OV model:

- `image_size`(`int`) : encoder native input resolution. The input is supposed to have 1:1 aspect ratio

### Decoder parameters

The following parameters can be provided via python API or RT Info embedded into OV model:

- `image_size`(`int`) : encoder native input resolution. The input is supposed to have 1:1 aspect ratio
- `mask_threshold`(`float`): threshold for generating hard predictions from output soft masks
- `embed_dim`(`int`) : size of the output embedding. This parameter is provided for convenience and should match
  the real output size.

## OV model specifications

### Encoder inputs

A single NCHW tensor representing a batch of images.

### Encoder outputs

A single NDHW, where D is the embedding dimension. HW is the output feature spatial resolution, which can differ from the input spatial resolution.

### Decoder inputs

Decoder OV model should have the following named inputs:

- `image_embeddings` (B, D, H, W) - embeddings obtained with encoder
- `point_coords` (B, N, 2) - 2D input prompts in XY format
- `point_labels` (B, N) - integer labels of input point prompts
- `mask_input` (B, 1, H, W) - mask for input embeddings
- `has_mask_input` (B, 1) - 0/1 flag enabling or disabling applying the `mask_input`
- `ori_shape` (B, 2) - resolution of the original image used as an input to the encoder wrapper.

### Decoder outputs

- `upscaled_masks` (B, N, H, W) - masks upscaled to `ori_shape`
- `iou_predictions` (B, N) - IoU predictions for the output masks
- `low_res_masks` (B, N, H, W) - masks in feature resolution

## How to use

See demos: [VPT](https://github.com/openvinotoolkit/model_api/tree/master/examples/python/visual_prompting)
and [ZSL-VPT](https://github.com/openvinotoolkit/model_api/tree/master/examples/python/zsl_visual_prompting)
