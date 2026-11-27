# Segmentation

The `SegmentationModel` is the OpenVINO wrapper for models exported from [OpenVINO Training Extensions](https://github.com/openvinotoolkit/training_extensions). It produces a segmentation mask for the input image.

## Model Specifications

### Inputs

A single input image of shape (H, W, 3) where H and W are the height and width of the image, respectively.

### Outputs

- `resultImage`: Image with the segmentation mask.
- `soft_prediction`: Soft prediction of the segmentation model.
- `saliency_map`: Saliency map of the input image.
- `feature_vector`: Feature vector of the input image. This is useful for Active Learning.

```{eval-rst}
.. automodule:: model_api.models.segmentation
   :members:
   :undoc-members:
   :show-inheritance:
```
