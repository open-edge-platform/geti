# Top-down keypoints detection

## Use case and high-level description

Keypoint detection model aims to detect a set of pre-defined keypoints on a cropped object.
If a crop is not tight enough, quality of keypoints degrades. Having this model and an
object detector, one can organize keypoint detection for all objects of interest presented on an image
(top-down approach).

## Models

Top-down keypoint detection pipeline uses detections that come from any appropriate detector,
and a keypoints regression model acting on crops.

### Keypoint model parameters

The following parameters can be provided via python API or RT Info embedded into OV model:

- `labels`(`list(str)`) : a list of keypoints names.

## OV model specifications

### Inputs

A single NCHW tensor representing a batch of images.

### Outputs

Two vectors in Simple Coordinate Classification Perspective ([SimCC](https://arxiv.org/abs/2107.03332)) format:

- `pred_x` (B, N, D1) - `x` coordinate representation, where `N` is the number of keypoints.
- `pred_y` (B, N, D2) - `y` coordinate representation, where `N` is the number of keypoints.

## How to use

```python
import cv2
from model_api.models import TopDownKeypointDetectionPipeline, Detection, KeypointDetectionModel

    model = KeypointDetectionModel.create_model("kp_model.xml")
    # a list of detections in (x_min, y_min, x_max, y_max, score, class_id) format
    detections = [Detection(0, 0, 100, 100, 1.0, 0)]
    top_down_pipeline = TopDownKeypointDetectionPipeline(model)
    predictions = top_down_detector.predict(image, detections)

    # iterating over a list of DetectedKeypoints. Each of the items corresponds to a detection
    for obj_keypoints in predictions:
        for point in obj_keypoints.keypoints.astype(np.int32):
            cv2.circle(
                image, point, radius=0, color=(0, 255, 0), thickness=5
            )
```
