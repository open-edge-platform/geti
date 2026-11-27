# Classification

## Description

The `ClassificationModel` is the OpenVINO wrapper for models exported from [OpenVINO Training Extensions](https://github.com/openvinotoolkit/training_extensions). It supports multi-label classification as well as hierarchical classification.

## Model Specifications

## Inputs

A single input image of shape (H, W, 3) where H and W are the height and width of the image, respectively.

## Outputs

- `top_labels`: List of tuples containing the top labels of the classification model.
- `saliency_map`: Saliency map of the input image.
- `feature_vector`: Feature vector of the input image. This is useful for Active Learning.
- `raw_scores`: Raw scores of the classification model.

```{eval-rst}
.. automodule:: model_api.models.classification
   :members:
   :undoc-members:
   :show-inheritance:
```
