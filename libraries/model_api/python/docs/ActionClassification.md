# ActionClassification Wrapper

## Use Case and High-Level Description

The `ActionClassificationModel` is a wrapper class designed for action classification models.
This class provides support for data preprocessing and postprocessing like other model wrapper classes.
Note that it isn't a subclass of `ImageModel`. It gets video as input so it is different than ImageModel.

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


## Arguments

- `labels`(`list[str]`) : List of class labels
- `path_to_labels` (`str`) : Path to file with labels. Labels are overrided if it's set.
- `mean_values` (`list[int | float]`) Normalization values to be subtracted from the image channels during preprocessing.
- `pad_value` (`int`) Pad value used during the resize resize_image_letterbox operation embedded within the model.
- `resize_type` (`str`) : The method of resizing the input image. Valid options include `crop`, `standard`, `fit_to_window`, and `fit_to_window_letterbox`.
- `reverse_input_channels` (`bool`) : Whether to reverse the order of input channels.
- `scale_values` (`list[int | float]`): Normalization values used to divide the image channels during preprocessing.

## Input format

The input format for action classification tasks differs from other vision tasks due to the nature of video data.
The input tensor includes additional dimensions to accommodate the video format.
It's often refered as single alphabet, and each alphabet means as below.

- N : Batch size
- S : Numer of clips x Number of crops
- C : Number of channels
- T : Time
- H : Height
- W : Width

The input should be provided as a single clip in THWC format.
Depending on the specified layout, the input will be transformed into either NSTHWC or NSCTHW format.
Unlike other vision model wrappers that utilize OpenVINO's PrePostProcessors (PPP) for preprocessing,
the ActionClassificationModel performs its preprocessing due to the current lack of video format support in OpenVINO PPP.

## output format

The output is encapsulated in a ClassificationResult object, which includes the indices, labels, and logits of the top predictions.
At present, saliency maps, feature vectors, and raw scores are not provided.
