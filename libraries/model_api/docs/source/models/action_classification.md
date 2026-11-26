# Action Classification

## Description

The `ActionClassificationModel` is a wrapper class designed for action classification models.
This class encapsulates preprocessing and postprocessing for action classification OpenVINO models satisfying a certain specification.
Unlike `ImageModel`, it accepts video clips as input, so it performs data preparation outside the OpenVINO graph.

## Parameters

The following parameters can be provided via Python API or RT Info embedded into an OpenVINO model:

- `labels` (`list[str]`): List of class labels.
- `path_to_labels` (`str`): Path to file with labels. Labels are overridden if this is set.
- `mean_values` (`list[int | float]`): Normalization values subtracted from image channels during preprocessing.
- `pad_value` (`int`): Pad value used during the `resize_image_letterbox` operation embedded within the model.
- `resize_type` (`str`): Resizing method. Valid options include `crop`, `standard`, `fit_to_window`, and `fit_to_window_letterbox`.
- `reverse_input_channels` (`bool`): Whether to reverse input channel order.
- `scale_values` (`list[int | float]`): Normalization values used to divide image channels during preprocessing.

## OpenVINO Model Specifications

### Inputs

A single 6D tensor with the following layout:

- `N`: Batch size.
- `S`: Number of clips x number of crops.
- `C`: Number of channels.
- `T`: Time.
- `H`: Height.
- `W`: Width.

`NSTHWC` layout is also supported.

### Outputs

A single tensor containing softmax-activated logits.

## Wrapper input-output specifications

### Inputs

A single clip in `THWC` format.

### Outputs

The output is represented as a `ClassificationResult` object, which includes the indices, labels, and logits of the top predictions.
At present, saliency maps, feature vectors, and raw scores are not provided.

## Example

```python
import cv2
import numpy as np

from model_api.adapters import OpenvinoAdapter, create_core
from model_api.models import ActionClassificationModel


model_path = "action_classification.xml"
inference_adapter = OpenvinoAdapter(create_core(), model_path, device="CPU")
action_cls_model = ActionClassificationModel(inference_adapter, preload=True)

cap = cv2.VideoCapture("sample.mp4")
input_data = np.stack([cap.read()[1] for _ in range(action_cls_model.clip_size)])

results = action_cls_model(input_data)
```

```{eval-rst}
.. automodule:: model_api.models.action_classification
   :members:
   :undoc-members:
   :show-inheritance:
```
