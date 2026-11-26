# Instance Segmentation

## Description

Instance segmentation model aims to detect and segment objects in an image. It is an extension of object detection, where each object is segmented into a separate mask. The model outputs a list of segmented objects, each containing a mask, bounding box, score and class label.

## OpenVINO Model Specifications

### Inputs

A single input image of shape (H, W, 3) where H and W are the height and width of the image, respectively.

### Outputs

Instance segmentation model outputs a `InstanceSegmentationResult` object containing the following attributes:

- `boxes` (np.ndarray) - Bounding boxes of the detected objects. Each in format of x1, y1, x2 y2.
- `scores` (np.ndarray) - Confidence scores of the detected objects.
- `masks` (np.ndarray) - Segmentation masks of the detected objects.
- `labels` (np.ndarray) - Class labels of the detected objects.
- `label_names` (list[str]) - List of class names of the detected objects.

## Example

```python
import cv2
from model_api.models import MaskRCNNModel

# Load the model
model = MaskRCNNModel.create_model("model.xml")

# Load image
image = cv2.imread("image.jpg")

# Forward pass
predictions = model(image)

# Iterate over the segmented objects
for box, score, mask, label, label_name in zip(
    predictions.boxes,
    predictions.scores,
    predictions.masks,
    predictions.labels,
    predictions.label_names,
):
    print(f"Box: {box}, Score: {score}, Label: {label}, Label Name: {label_name}")
    cv2.imshow("Mask", mask)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
```

```{eval-rst}
.. automodule:: model_api.models.instance_segmentation
   :members:
   :undoc-members:
   :show-inheritance:
```
