# YOLO-DETR

YOLO-DETR wraps detection models that export decoded query predictions as a single
`[1, N, 6]` tensor. Each prediction row contains:

```text
[cx, cy, width, height, confidence, class_id]
```

The box coordinates are normalized to the model input dimensions. The wrapper
converts them to `xyxy` coordinates, applies the configured confidence threshold,
and rescales them to the original image dimensions.

The wrapper uses `fit_to_window_letterbox` resizing and a default confidence
threshold of `0.5`. Non-maximum suppression is disabled by default because the
YOLO-DETR decoder already selects its query predictions. It can be enabled
explicitly with `nms_execute=True` when required by a downstream workflow.

```python
from model_api.models import Model

model = Model.create_model("yolo_detr.xml")
result = model(image)
```

The exported model should contain `YOLODETR` in
`model_info.model_type`, allowing `Model.create_model()` to select this wrapper
automatically.

```{eval-rst}
.. automodule:: model_api.models.yolo_detr
   :members:
   :undoc-members:
   :show-inheritance:
```
