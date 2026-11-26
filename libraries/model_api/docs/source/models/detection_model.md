# Detection Model

## Description

Detection model aims to detect objects in an image. The model outputs a list of detected objects, each containing a bounding box, score and class label.

## OpenVINO Model Specifications

### Inputs

A single input image of shape (H, W, 3) where H and W are the height and width of the image, respectively.

### Outputs

Detection model outputs a `DetectionResult` objects containing the following attributes:

- `boxes` (np.ndarray) - Bounding boxes of the detected objects. Each in format of x1, y1, x2 y2.
- `scores` (np.ndarray) - Confidence scores of the detected objects.
- `labels` (np.ndarray) - Class labels of the detected objects.
- `label_names` (list[str]) - List of class names of the detected objects.

## Example

```python
import cv2
from model_api.models import SSD

# Load the model
model = SSD.create_model("model.xml")

# Forward pass
predictions = model(image)

# Iterate over detection result
for box, score, label, label_name in zip(
    predictions.boxes,
    predictions.scores,
    predictions.labels,
    predictions.label_names,
):
    print(f"Box: {box}, Score: {score}, Label: {label}, Label Name: {label_name}")
```

```{eval-rst}
.. automodule:: model_api.models.detection_model
   :members:
   :undoc-members:
   :show-inheritance:
```
