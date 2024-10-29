# ActionClassification Wrapper

## Use case and high-level description

The `ActionClassificationModel` is a wrapper class designed for action classification models.
This class allows to encapsulate data pre-and post processing for action classification OpenVINO models satisfying
a certain specifications.
Note that it isn't a subclass of `ImageModel`. It gets video as input so it is different than ImageModel.
Also, it doesn't use OV.PrePostProcessor() and therefore performs data preparation steps outside of OV graph.

## Model parameters

The following parameters can be provided via python API or RT Info embedded into OV model:

- `labels`(`list[str]`) : List of class labels
- `path_to_labels` (`str`) : Path to file with labels. Labels are overridden if it's set.
- `mean_values` (`list[int | float]`) Normalization values to be subtracted from the image channels during preprocessing.
- `pad_value` (`int`) Pad value used during the resize resize_image_letterbox operation embedded within the model.
- `resize_type` (`str`) : The method of resizing the input image. Valid options include `crop`, `standard`, `fit_to_window`, and `fit_to_window_letterbox`.
- `reverse_input_channels` (`bool`) : Whether to reverse the order of input channels.
- `scale_values` (`list[int | float]`): Normalization values used to divide the image channels during preprocessing.

## OV Model specifications

### Inputs

A single 6D tensor with the following layout:

- N : Batch size
- S : Numer of clips x Number of crops
- C : Number of channels
- T : Time
- H : Height
- W : Width

NSTHWC is layout is also supported.

### Outputs

A single tensor containing softmax-activated logits.

## Wrapper input-output specifications

### Inputs

A single clip in THWC format.

### Outputs

The output is represented as a `ClassificationResult` object, which includes the indices, labels, and logits of the top predictions.
At present, saliency maps, feature vectors, and raw scores are not provided.

## How to use

Utilizing the ActionClassificationModel is similar to other model wrappers, with the primary difference being the preparation of video clip inputs instead of single images.

Below is an example demonstrating how to initialize the model with OpenVINO IR files and classify actions in a video clip.

```python
import cv2
import numpy as np
# import model wrapper class
from model_api.models import ActionClassificationModel
# import inference adapter and helper for runtime setup
from model_api.adapters import OpenvinoAdapter, create_core


# define the path to action classification model in IR format
model_path = "action_classification.xml"

# create adapter for OpenVINO runtime, pass the model path
inference_adapter = OpenvinoAdapter(create_core(), model_path, device="CPU")

# instantiate the ActionClassificationModel wrapper
# setting preload=True loads the model onto the CPU within the adapter0
action_cls_model = ActionClassificationModel(inference_adapter, preload=True)

# load video and make a clip as input
cap = cv2.VideoCapture("sample.mp4")
input_data = np.stack([cap.read()[1] for _ in range(action_cls_model.clip_size)])

# perform preprocessing, inference, and postprocessing
results = action_cls_model(input_data)
```

As illustrated, initializing the model and performing inference can be achieved with minimal code.
The wrapper class takes care of input processing, layout adjustments, and output processing automatically.
