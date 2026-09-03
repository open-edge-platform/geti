# Getting started

## Install

```bash
pip install getitrack
```

For development from a checkout, use `just venv`, then `just lint` and `just test-unit`.

## Construct a tracker

A tracker is built from a `TrackerConfig`. The quickest path is `BaseTracker.from_config`, which accepts a config object, a plain dict, or a path to a YAML file, and dispatches on the `algorithm` key (`core/base.py:117`).

```python
from getitrack import BaseTracker

# From a dict (algorithm defaults to bytetrack).
tracker = BaseTracker.from_config({"algorithm": "bytetrack"})

# From a YAML file.
tracker = BaseTracker.from_config("configs/bytetrack.yaml")
```

You can also build a typed config and pass it in:

```python
from getitrack import BaseTracker
from getitrack.algorithms.configs.bytetrack import ByteTrackConfig
from getitrack.config import LifecycleConfig

config = ByteTrackConfig(lifecycle=LifecycleConfig(max_age=15, min_hits=2))
tracker = BaseTracker.from_config(config)
```

Concrete tracker classes (`ByteTrackTracker`, `SortTracker`, `OCSortTracker`) can also be constructed directly with their config. `from_config` selects the class from the `algorithm` key.

## Run the per-frame loop

Detection is external. Build one `Detections` per frame from your detector's boxes, then call `update`:

```python
import numpy as np
from getitrack import BaseTracker
from getitrack.core.detection import Detections

tracker = BaseTracker.from_config({"algorithm": "bytetrack"})

for frame_id, boxes_scores_classes in enumerate(your_detector_stream()):
    boxes, scores, class_ids = boxes_scores_classes
    detections = Detections(
        bboxes=boxes.astype(np.float32),        # (N, 4) xyxy, absolute pixels
        scores=scores.astype(np.float32),       # (N,) in [0, 1]
        class_ids=class_ids.astype(np.int64),   # (N,)
        frame_id=frame_id,
    )
    tracked = tracker.update(detections)
    for i in range(len(tracked)):
        print(tracked.frame_id, int(tracked.track_ids[i]), tracked.bboxes[i])
```

`Detections.create_empty(frame_id)` builds an empty batch for frames with no detections; keep calling `update` on those so tracks age correctly.

Call `tracker.reset()` between independent sequences to clear all state and restart id allocation (`core/base.py:105`).

## Using a detector adapter

A `DetectionAdapter` (`adapters/base.py:22`) wraps a detector and turns a raw BGR frame into `Detections`:

```python
detections = adapter.detect(frame_bgr, frame_id)
tracked = tracker.update(detections)
```

getitrack ships `GetiAdapter` (`adapters/geti.py:50`) for a getitune detection model. Any other framework is supported by subclassing `DetectionAdapter`.

## Bounding-box convention

Boxes are always `(N, 4)` in `xyxy` order (`[x1, y1, x2, y2]`, with `x1 < x2` and `y1 < y2`) in absolute pixel coordinates. Convert other formats at the boundary before building `Detections`; validation in `__post_init__` rejects malformed boxes early.
