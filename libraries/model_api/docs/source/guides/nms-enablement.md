# NMS Enablement

Detection and InstanceSegmentation models support non-maximum suppression (NMS) postprocessing step, which allows to filter model predictions based on confidence scores and bounding box overlap. NMS can be enabled or disabled via model configuration parameters, which are described in details below.

## Model configuration parameters for NMS

NMS-related parameters are available for `DetectionModel` and its subclasses, `MaskRCNNModel` and its subclasses, `YOLO` and its subclasses. Below is the list of NMS-related parameters for these models:

1. `nms_execute`: bool - should non-maximum suppression (NMS) be applied in postprocessing or not. If False, raw model output will be returned without NMS filtering
1. `iou_threshold`: float - threshold for non-maximum suppression (NMS) intersection over union (IOU) filtering
1. `agnostic_nms`: bool - if True, NMS will be class agnostic, otherwise it will be applied separately for each class
1. `nms_max_predictions`: int - maximum number of predictions after NMS. If 0, no limit will be applied

## Example of NMS enablement via `model_info` section

To enable NMS for a model, you may set the parameters described above in the `model_info` section of the model configuration file. Below is an example of how to enable NMS for a detection model:

```xml
<model_info>
    (...)
    <nms_execute value="True" />
    <iou_threshold value="0.7" />
    <agnostic_nms value="True" />
    <nms_max_predictions value="0" />
</model_info>
```

In this example, NMS is enabled with an IOU threshold of 0.7, class agnostic filtering (which means all classes are treated as one), and no limit on the number of predictions after NMS.

## Example of NMS enablement via configuration argument

To enable NMS for a model, you may set the parameters described above in `configuration` argument of the model constructor. Below is an example of how to enable NMS for a detection model with the same values as in the previous example:

```python
import cv2
from model_api.models import Model

# 1. Load model
model = Model.create_model(
    "model.xml",
    device="CPU",
    configuration={
        "nms_execute": True,
        "iou_threshold": 0.7,
        "agnostic_nms": True,
        "nms_max_predictions": 0,
    }
)

# 2. Load image
image = cv2.imread("image.jpg")

# 3. Run inference
result = model(image)
```
