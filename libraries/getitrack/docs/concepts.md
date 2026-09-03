# Concepts

## Detections and TrackedDetections

The two containers are defined in `core/detection.py`.

- `Detections` is what the detector saw: boxes, scores, class ids, and a `frame_id`. There are no track ids.
- `TrackedDetections` is what the tracker decided: the detection fields plus a mandatory `track_id` and `track_state` per row, and optional `det_indices` and `interpolated`.

`TrackedDetections` is not a subclass of `Detections`.

Both are numpy dataclasses with eager validation in `__post_init__`: shape, dtype (enforced, not coerced), row alignment, and value ranges are checked at construction, so malformed inputs fail at the boundary rather than deep inside the Kalman math.

Fields, dtypes, and shapes:

| Container | Field | Shape | Dtype | Notes |
| --- | --- | --- | --- | --- |
| Detections | bboxes | (N, 4) | float32 | xyxy, absolute pixels |
| Detections | scores | (N,) | float32 | in [0, 1] |
| Detections | class_ids | (N,) | int64 | |
| Detections | frame_id | scalar | int | |
| Detections | embeddings | (N, D) | float32 | optional appearance features |
| TrackedDetections | track_ids | (N,) | int64 | stable per-object id |
| TrackedDetections | track_states | (N,) | int8 | `TrackState` values |
| TrackedDetections | det_indices | (N,) | int64 | optional; row into the frame's input `Detections`, -1 if none |
| TrackedDetections | interpolated | (N,) | bool | optional; set by the interpolation stage |

Helper methods you will use:

- `Detections`: `filter_by_score`, `split_by_score` (ByteTrack's high and low split), `filter_by_class`, `select`, `create_empty`, `len()`.
- `TrackedDetections`: `active_only` (rows in `ACTIVE` state), `to_string_states` (lowercase state names), `create_empty`, `len()`.

## The track lifecycle

Each tracked object is a `Track` (`core/track.py:46`) with a lifecycle `state`, plus counters `age`, `hits`, and `time_since_update`. The states are a `TrackState` int enum (`core/track.py:33`): `TENTATIVE` (0), `ACTIVE` (1), `LOST` (2), `REMOVED` (3).

Transitions (algorithm-agnostic, driven by `mark_hit` and `mark_miss`):

| From | Event | To |
| --- | --- | --- |
| TENTATIVE | reaches `min_hits` observed detections | ACTIVE |
| TENTATIVE | missed for more than `tentative_max_age` frames | REMOVED |
| ACTIVE | missed this frame | LOST |
| LOST | observed again | ACTIVE |
| LOST | missed for more than `max_age` frames | REMOVED |

A new track starts `TENTATIVE`. `min_hits`, `tentative_max_age`, and `max_age` come from `LifecycleConfig` (see [Configuration](configuration.md)). Trackers may bypass `min_hits` on the first frame of a sequence so objects present from the start get ids immediately.

## det_indices and class_filter

`update` applies `class_filter` before the algorithm runs, so excluded classes never spawn or match tracks. The `det_indices` on the output always index into the unfiltered `Detections` you passed to `update`, because the base remaps them back from filtered-row space (`core/base.py:74`). Use `det_indices` to re-attach per-detection data (embeddings, masks) to the resulting tracks; a value of -1 marks a row with no source detection this frame.

## frame_id semantics

`frame_id` is carried on every `Detections` and `TrackedDetections`. It must be monotonic across a sequence but need not be contiguous, so dropped or skipped frames are safe. Reset the tracker (`reset()`) at a true sequence boundary rather than reusing one instance across unrelated videos.

## Embeddings

`Detections.embeddings` is an optional `(N, D)` float32 array of per-detection appearance features. Motion-only trackers (ByteTrack, SORT, OC-SORT) ignore it. Appearance-based association is on the [Roadmap](roadmap.md).
