# Configuration

Configuration is a set of Pydantic models in `config.py` (shared) and `algorithms/configs/` (per algorithm). Models reject unknown keys and validate types and ranges at construction. Every field below is sourced from the actual model definition.

## Enums

`AlgorithmType` (`config.py:24`): `bytetrack`, `sort`, `ocsort`, `botsort`, `memory`. Only `bytetrack`, `sort`, and `ocsort` are registered and usable on this release; `botsort` and `memory` are reserved for in-flight work (see [Roadmap](roadmap.md)).

`DistanceMetric` (`config.py:42`): `iou`, `giou`, `diou`, `ciou`.

`InterpolationMethod` (`config.py:34`): `linear`, `kalman`, `spline`.

## TrackerConfig (shared base)

Common to every algorithm (`config.py:111`).

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| algorithm | AlgorithmType | (set per subclass) | Which tracker to build. |
| verbose | bool | False | Log a one-line per-frame summary at INFO on the `getitrack` logger. |
| class_filter | list[int] or None | None | Track only these class ids; None tracks all. Applied before association. |
| score_threshold | float [0, 1] | 0.1 | Low-score floor; detections at or below this are excluded. |
| distance_metric | DistanceMetric | iou | Pairwise box distance used for association. |
| lifecycle | LifecycleConfig | defaults | Track creation, confirmation, and removal. |
| motion | MotionConfig | defaults | Kalman and motion-model parameters. |
| interpolation | InterpolationConfig | defaults | Interpolation parameters (inert until the interpolation stage lands, see Roadmap). |

## LifecycleConfig (`config.py:63`)

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| max_age | int >= 1 | 30 | Consecutive missed frames a LOST track may accumulate before removal. |
| min_hits | int >= 1 | 2 | Observed detections to promote TENTATIVE to ACTIVE. |
| tentative_max_age | int >= 0 | 0 | Missed frames a TENTATIVE track tolerates before removal. 0 removes on the first miss. |

## MotionConfig (`config.py:78`)

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| process_noise | float > 0 | 1.0 | Multiplier on the process-noise covariance (Q). Larger trusts observations over the motion prior. |
| measurement_noise | float > 0 | 1.0 | Multiplier on the measurement-noise covariance (R). Larger trusts the motion prior over observations. |
| velocity_decay | float (0, 1] | 1.0 | Per-frame velocity damping. 1.0 applies no damping; below 1.0 models deceleration. |

## InterpolationConfig (`config.py:92`)

Present on `TrackerConfig` but not consumed on this release; the interpolation post-processing stage is an in-flight PR (see [Roadmap](roadmap.md)).

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| enabled | bool | True | Enable the interpolation stage. |
| method | InterpolationMethod | linear | Interpolation strategy. |
| max_gap | int >= 1 | 5 | Maximum consecutive missing frames bridged. |
| smoothing_window | int >= 1 | 5 | Window for spline or moving-average smoothing. |
| online_buffer | int >= 0 | 0 | Frames of lookahead in online mode; 0 is strictly causal. |

## ByteTrackConfig (`algorithms/configs/bytetrack.py`)

Adds to `TrackerConfig`:

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| algorithm | literal | bytetrack | Fixed. |
| match_threshold | float [0, 2.5] | 0.8 | Maximum assignment cost accepted. Allows above 1.0 for the wider-range metrics. |
| high_score_threshold | float [0, 1] | 0.5 | High and low split for two-stage association. Spawning a new track needs a score 0.1 above this. |
| match_class_only | bool | True | Restrict matching to same-class pairs. |

Validation: `score_threshold` must be below `high_score_threshold`, and `high_score_threshold` must leave room for the 0.1 new-track margin (at most 0.9).

## SortConfig (`algorithms/configs/sort.py`)

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| algorithm | literal | sort | Fixed. |
| iou_threshold | float [0, 1] | 0.3 | Minimum IoU for a valid association. The internal `match_threshold` is `1 - iou_threshold`. |
| match_class_only | bool | True | Restrict matching to same-class pairs. |

## OCSortConfig (`algorithms/configs/ocsort.py`)

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| algorithm | literal | ocsort | Fixed. |
| det_threshold | float [0, 1] | 0.6 | High-score gate; detections above it drive the first pass and can spawn tracks. |
| iou_threshold | float [0, 1] | 0.3 | Minimum IoU for a valid association. |
| delta_t | int >= 1 | 3 | Frame gap used to estimate motion direction for the OCM term. |
| inertia | float [0, 1] | 0.2 | Weight of the OCM velocity-direction term. |
| use_byte | bool | False | Associate low-score detections to unmatched tracks before the recovery pass. |
| match_class_only | bool | True | Restrict matching to same-class pairs. |

Validation: `score_threshold` must be below `det_threshold`.

## YAML load and save

`TrackerConfig.from_yaml(path)` reads a YAML file, dispatches on the `algorithm` key (default `bytetrack`), and validates against that algorithm's config. `config.to_yaml(path)` writes it back.

```yaml
# bytetrack.yaml
algorithm: bytetrack
score_threshold: 0.1
distance_metric: iou
high_score_threshold: 0.5
match_threshold: 0.8
lifecycle:
  max_age: 30
  min_hits: 2
motion:
  process_noise: 1.0
  velocity_decay: 1.0
```

```python
from getitrack.config import TrackerConfig

config = TrackerConfig.from_yaml("bytetrack.yaml")   # returns a ByteTrackConfig
config.to_yaml("out.yaml")
```

A minimal config is just `algorithm: bytetrack`; every other field falls back to its default.
